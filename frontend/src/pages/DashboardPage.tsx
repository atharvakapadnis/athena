import { useQuery } from '@tanstack/react-query';
import { Typography, Grid, Box, Button, Card, CardContent, Alert } from '@mui/material';
import { Refresh } from '@mui/icons-material';
import { usePageTitle } from '@/hooks/use-page-title';
import { dashboardService } from '@/services/api';
import { QUERY_KEYS } from '@/constants';

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
        <Card>
          <CardContent>
            <Typography>Loading dashboard data...</Typography>
          </CardContent>
        </Card>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Error loading dashboard: {(error as any)?.message || 'Unknown error'}
        </Alert>
      )}

      {dashboardData && (
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  System Overview
                </Typography>
                <Typography variant="body1">
                  Dashboard data loaded successfully!
                </Typography>
                <pre style={{ fontSize: '12px', marginTop: '10px' }}>
                  {JSON.stringify(dashboardData, null, 2)}
                </pre>
              </CardContent>
            </Card>
          </Grid>
          
          <Grid size={{ xs: 12, md: 6 }}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  System Status
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Last Updated: {dashboardData.last_updated ? new Date(dashboardData.last_updated).toLocaleString() : 'Unknown'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}
    </Box>
  );
}