import { useQuery } from '@tanstack/react-query';
import { Typography, Grid, Box, Button } from '@mui/material';
import { Refresh } from '@mui/icons-material';
import { usePageTitle } from '@/hooks/use-page-title';
import { dashboardService } from '@/services/api';
import { QUERY_KEYS } from '@/constants';
import { SystemOverviewCard } from '@/components/dashboard/SystemOverview';
import { PerformanceMetricsCard } from '@/components/dashboard/PerformanceMetrics';

export function DashboardPage() {
  usePageTitle('Dashboard');

  const {
    data: dashboardData,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: QUERY_KEYS.DASHBOARD_SUMMARY,
    queryFn: dashboardService.getSummary,
    refetchInterval: 60000, // Auto-refresh every 60 seconds
    staleTime: 30000, // Consider data stale after 30 seconds
  });

  const handleRefresh = () => {
    refetch();
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Dashboard
        </Typography>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={handleRefresh}
          disabled={isLoading}
        >
          Refresh
        </Button>
      </Box>

      {isLoading && !dashboardData && (
        <Typography>Loading dashboard data...</Typography>
      )}

      {error && (
        <Typography color="error" sx={{ mb: 2 }}>
          Error loading dashboard: {(error as any)?.message || 'Unknown error'}
        </Typography>
      )}

      {dashboardData && (
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6 }}>
            <SystemOverviewCard
              data={dashboardData.system_overview}
              isLoading={isLoading}
              error={error ? (error as any)?.message : null}
            />
          </Grid>
          
          <Grid size={{ xs: 12, md: 6 }}>
            <PerformanceMetricsCard
              data={dashboardData.performance_metrics}
              isLoading={isLoading}
              error={error ? (error as any)?.message : null}
            />
          </Grid>

          <Grid size={{ xs: 12 }}>
            <Typography variant="h6">
              Last Updated: {dashboardData.last_updated ? new Date(dashboardData.last_updated).toLocaleString() : 'Unknown'}
            </Typography>
          </Grid>

          {dashboardData.recommendations && dashboardData.recommendations.length > 0 && (
            <Grid size={{ xs: 12 }}>
              <Typography variant="h6" gutterBottom>
                Recommendations
              </Typography>
              {dashboardData.recommendations.map((recommendation, index) => (
                <Typography key={index} variant="body2" sx={{ mb: 1 }}>
                  • {recommendation}
                </Typography>
              ))}
            </Grid>
          )}
        </Grid>
      )}
    </Box>
  );
}