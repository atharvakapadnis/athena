import { Card, CardContent, Typography, Grid, Box } from '@mui/material';
import type { SystemOverview } from '@/types';

interface SystemOverviewProps {
  data: SystemOverview;
  isLoading: boolean;
  error: string | null;
}

export function SystemOverviewCard({ data, isLoading, error }: SystemOverviewProps) {
  if (isLoading) return <Typography>Loading system overview...</Typography>;
  if (error) return <Typography color="error">Error: {error}</Typography>;

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          System Overview
        </Typography>
        <Grid container spacing={2}>
          <Grid size={{ xs: 6 }}>
            <Box>
              <Typography variant="h4" color="primary">
                {data.total_batches}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Batches
              </Typography>
            </Box>
          </Grid>
          <Grid size={{ xs: 6 }}>
            <Box>
              <Typography variant="h4" color="primary">
                {data.total_items}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total Items
              </Typography>
            </Box>
          </Grid>
          <Grid size={{ xs: 6 }}>
            <Box>
              <Typography variant="h4" color="primary">
                {(data.success_rate * 100).toFixed(1)}%
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Success Rate
              </Typography>
            </Box>
          </Grid>
          <Grid size={{ xs: 6 }}>
            <Box>
              <Typography variant="h4" color="primary">
                {data.average_confidence.toFixed(2)}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Avg Confidence
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
}