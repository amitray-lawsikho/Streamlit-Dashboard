"use client"

import { useState, useMemo } from "react"
import useSWR from "swr"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { DashboardHeader } from "@/components/dashboard/dashboard-header"
import { DashboardFilters } from "@/components/dashboard/dashboard-filters"
import { MetricCards } from "@/components/dashboard/metric-cards"
import { TeamSummaryChart } from "@/components/dashboard/analytics-charts"
import { AgentLogsTable } from "@/components/dashboard/agent-logs-table"
import { AIInsightsSidebar } from "@/components/dashboard/ai-insights-sidebar"
import { LayoutDashboard, ScrollText, Sparkles } from "lucide-react"

interface LogEntry {
  id: string
  "CALLER": string
  "TEAM": string
  "VERTICAL": string
  "IN/OUT TIME": {
    in: string
    out: string
  }
  "CALL STATUS": string
  "DURATION_MINUTES": number
  "REMARKS": string | null
}

interface TeamSummary {
  team: string
  total_calls: number
  connected: number
  productive_calls: number
  pick_up_ratio: number
}

interface MetricsData {
  metrics: {
    "TOTAL CALLS": number
    "PICK UP RATIO %": number
    "CALL DURATION > 3 MINS": number
    "PRODUCTIVE HOURS": number
  }
  team_summary: TeamSummary[]
  teams: string[]
  verticals: string[]
  logs: LogEntry[]
}

const fetcher = async (url: string) => {
  const res = await fetch(url)
  if (!res.ok) throw new Error("Failed to fetch metrics")
  return res.json()
}

export default function DashboardPage() {
  const { data, error, isLoading, mutate } = useSWR<MetricsData>("/api/metrics", fetcher, {
    refreshInterval: 30000,
  })

  const [activeTab, setActiveTab] = useState("overview")
  const [selectedTeam, setSelectedTeam] = useState("all")
  const [selectedVertical, setSelectedVertical] = useState("all")
  const [selectedDateRange, setSelectedDateRange] = useState("7d")

  const handleRefresh = () => {
    mutate()
  }

  const handleResetFilters = () => {
    setSelectedTeam("all")
    setSelectedVertical("all")
    setSelectedDateRange("7d")
  }

  // Filter logs based on selected filters
  const filteredData = useMemo(() => {
    if (!data || !data.logs || !data.teams) return null

    let filteredLogs = [...data.logs]

    if (selectedTeam !== "all") {
      filteredLogs = filteredLogs.filter((log) => log["TEAM"] === selectedTeam)
    }

    if (selectedVertical !== "all") {
      filteredLogs = filteredLogs.filter((log) => log["VERTICAL"] === selectedVertical)
    }

    // Recalculate metrics based on filtered logs
    const totalCalls = filteredLogs.length
    const connectedCalls = filteredLogs.filter((log) => log["CALL STATUS"] === "Connected").length
    const pickUpRatio = totalCalls > 0 ? parseFloat(((connectedCalls / totalCalls) * 100).toFixed(1)) : 0
    const callsOver3Mins = filteredLogs.filter((log) => log.DURATION_MINUTES > 3).length
    const productiveMinutes = filteredLogs
      .filter((log) => log.DURATION_MINUTES > 3)
      .reduce((acc, log) => acc + log.DURATION_MINUTES, 0)
    const productiveHours = parseFloat((productiveMinutes / 60).toFixed(1))

    // Recalculate team summary for filtered data
    const teamSummary = (data.teams || []).map((team) => {
      const teamLogs = filteredLogs.filter((log) => log["TEAM"] === team)
      const teamConnected = teamLogs.filter((l) => l["CALL STATUS"] === "Connected").length
      const teamProductiveCalls = teamLogs.filter((l) => l.DURATION_MINUTES > 3).length
      return {
        team,
        total_calls: teamLogs.length,
        connected: teamConnected,
        productive_calls: teamProductiveCalls,
        pick_up_ratio: teamLogs.length > 0 ? parseFloat(((teamConnected / teamLogs.length) * 100).toFixed(1)) : 0,
      }
    })

    return {
      metrics: {
        "TOTAL CALLS": totalCalls,
        "PICK UP RATIO %": pickUpRatio,
        "CALL DURATION > 3 MINS": callsOver3Mins,
        "PRODUCTIVE HOURS": productiveHours,
      },
      team_summary: teamSummary,
      logs: filteredLogs,
    }
  }, [data, selectedTeam, selectedVertical])

  if (error) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <p className="text-destructive text-lg">Failed to load metrics</p>
          <p className="text-muted-foreground text-sm mt-1">Please try again later</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <div className="mx-auto max-w-[1600px] p-6">
        <DashboardHeader onRefresh={handleRefresh} isLoading={isLoading} />

        {isLoading || !data || !filteredData ? (
          <div className="mt-8 space-y-6">
            <div className="h-14 rounded-lg bg-card border border-border animate-pulse" />
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <div
                  key={i}
                  className="h-24 rounded-lg bg-card border border-border animate-pulse"
                />
              ))}
            </div>
            <div className="h-[400px] rounded-lg bg-card border border-border animate-pulse" />
          </div>
        ) : (
          <>
            <div className="mt-6">
              <DashboardFilters
                teams={data.teams}
                verticals={data.verticals}
                selectedTeam={selectedTeam}
                selectedVertical={selectedVertical}
                selectedDateRange={selectedDateRange}
                onTeamChange={setSelectedTeam}
                onVerticalChange={setSelectedVertical}
                onDateRangeChange={setSelectedDateRange}
                onReset={handleResetFilters}
              />
            </div>

            <div className="mt-6">
              <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                <TabsList className="bg-secondary border border-border mb-6">
                  <TabsTrigger
                    value="overview"
                    className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground gap-2"
                  >
                    <LayoutDashboard className="h-4 w-4" />
                    Overview Dashboard
                  </TabsTrigger>
                  <TabsTrigger
                    value="logs"
                    className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground gap-2"
                  >
                    <ScrollText className="h-4 w-4" />
                    Detailed Agent Logs
                  </TabsTrigger>
                  <TabsTrigger
                    value="insights"
                    className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground gap-2"
                  >
                    <Sparkles className="h-4 w-4" />
                    AI Insights
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="mt-0 space-y-6">
                  <MetricCards metrics={filteredData.metrics} />
                  <TeamSummaryChart teamSummary={filteredData.team_summary} />
                </TabsContent>

                <TabsContent value="logs" className="mt-0">
                  <AgentLogsTable logs={filteredData.logs} />
                </TabsContent>

                <TabsContent value="insights" className="mt-0">
                  <div className="max-w-xl">
                    <AIInsightsSidebar logs={filteredData.logs} metrics={filteredData.metrics} />
                  </div>
                </TabsContent>
              </Tabs>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
