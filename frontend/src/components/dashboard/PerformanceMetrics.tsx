import { Card, CardContent, Typography, Grid, Box } from '@mui/material';
import type { PerformanceMetrics } from '@/types';

interface PerformanceMetricsProps {
  data: PerformanceMetrics;
  isLoading: boolean;
  error: string | null;
}

export function PerformanceMetricsCard({ data, isLoading, error }: PerformanceMetricsProps) {
  if (isLoading) return <Typography>Loading performance metrics...</Typography>;
  if (error) return <Typography color="error">Error: {error}</Typography>;

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Performance Metrics
        </Typography>
        <Grid container spacing={2}>
          <Grid size={{ xs: 6 }}>
            <Box>
              <Typography variant="h4" color="secondary">
                {data.processing_speed.toFixed(2)}s
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Avg Processing Time
              </Typography>
            </Box>
          </Grid>
          <Grid size={{ xs: 6 }}>
            <Box>
              <Typography variant="h4" color="secondary">
                {data.throughput.toFixed(0)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Items/Hour
              </Typography>
            </Box>
          </Grid>
          <Grid size={{ xs: 6 }}>
            <Box>
              <Typography variant="h4" color="secondary">
                {(data.error_rate * 100).toFixed(1)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Error Rate
              </Typography>
            </Box>
          </Grid>
          <Grid size={{ xs: 6 }}>
            <Box>
              <Typography variant="h4" color="secondary">
                {data.efficiency_score.toFixed(1)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Efficiency Score
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}