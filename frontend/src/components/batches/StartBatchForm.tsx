import { useState } from 'react';
import {
    Card,
    CardContent,
    Typography,
    TextField,
    Button,
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    FormControlLabel,
    Checkbox,
    Grid,
    Alert,
    CircularProgress,
    Box
} from '@mui/material';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { batchService } from '@/services/api';
import { QUERY_KEYS } from '@/constants';
import { DEFAULT_BATCH_CONFIG, PRIORITY_OPTIONS } from '@/constants/batch-config';
import type { BatchConfig } from '@/types';

interface StartBatchFormProps {
    onSuccess?: (batch: any) => void;
}

export function StartBatchForm({ onSuccess }: StartBatchFormProps) {
    const [config, setConfig] = useState<BatchConfig>(DEFAULT_BATCH_CONFIG);
    const [error, setError] = useState<string>('');
    const queryClient = useQueryClient();
  
    const startBatchMutation = useMutation({
      mutationFn: batchService.startBatch,
      onSuccess: async (batch) => {
        setError('');

        // Wait for the batch to be fully saved
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Force invalidate with exact query keys
        await queryClient.invalidateQueries({ 
          queryKey: QUERY_KEYS.BATCH_QUEUE,
          exact: false,
          refetchType: 'all'
        });
        
        await queryClient.invalidateQueries({ 
          queryKey: QUERY_KEYS.BATCH_HISTORY,
          exact: false,
          refetchType: 'all'
        });

      //Trigger the parents onSuccess callback
      if (onSuccess) {
        onSuccess(batch);
      }
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to start batch');
    },
    });
  
    const handleSubmit = (e: React.FormEvent) => {
      e.preventDefault();
      setError('');
      startBatchMutation.mutate(config);
    };
  
    const handleChange = (field: keyof BatchConfig) => (
      e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
    ) => {
      const value = e.target.type === 'checkbox' 
        ? (e.target as HTMLInputElement).checked
        : e.target.type === 'number'
        ? Number(e.target.value)
        : e.target.value;
  
      setConfig(prev => ({
        ...prev,
        [field]: value,
      }));
    };
  
    const resetToDefaults = () => {
      setConfig(DEFAULT_BATCH_CONFIG);
      setError('');
    };
  
    return (
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Start New Batch
            </Typography>
            <Button
              variant="outlined"
              size="small"
              onClick={resetToDefaults}
              disabled={startBatchMutation.isPending}
            >
              Reset to Defaults
            </Button>
          </Box>
  
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
  
          <Box component="form" onSubmit={handleSubmit}>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Batch Size"
                  type="number"
                  value={config.batch_size}
                  onChange={handleChange('batch_size')}
                  inputProps={{ min: 1, max: 1000 }}
                  disabled={startBatchMutation.isPending}
                  helperText="Number of items to process in this batch"
                />
              </Grid>
  
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Start Index"
                  type="number"
                  value={config.start_index}
                  onChange={handleChange('start_index')}
                  inputProps={{ min: 0 }}
                  disabled={startBatchMutation.isPending}
                  helperText="Starting position in the dataset"
                />
              </Grid>
  
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="High Confidence Threshold"
                  type="number"
                  value={config.confidence_threshold_high}
                  onChange={handleChange('confidence_threshold_high')}
                  inputProps={{ min: 0, max: 1, step: 0.01 }}
                  disabled={startBatchMutation.isPending}
                  helperText="Threshold for high confidence (0.0 - 1.0)"
                />
              </Grid>
  
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Medium Confidence Threshold"
                  type="number"
                  value={config.confidence_threshold_medium}
                  onChange={handleChange('confidence_threshold_medium')}
                  inputProps={{ min: 0, max: 1, step: 0.01 }}
                  disabled={startBatchMutation.isPending}
                  helperText="Threshold for medium confidence (0.0 - 1.0)"
                />
              </Grid>
  
              <Grid size={{ xs: 12, md: 6 }}>
                <TextField
                  fullWidth
                  label="Max Processing Time (seconds)"
                  type="number"
                  value={config.max_processing_time}
                  onChange={handleChange('max_processing_time')}
                  inputProps={{ min: 60, max: 3600 }}
                  disabled={startBatchMutation.isPending}
                  helperText="Maximum time allowed for batch processing"
                />
              </Grid>
  
              <Grid size={{ xs: 12, md: 6 }}>
                <FormControl fullWidth disabled={startBatchMutation.isPending}>
                  <InputLabel>Priority</InputLabel>
                  <Select
                    value={config.priority}
                    label="Priority"
                    onChange={(e) => setConfig(prev => ({ ...prev, priority: e.target.value as any }))}
                  >
                    {PRIORITY_OPTIONS.map((option) => (
                      <MenuItem key={option.value} value={option.value}>
                        {option.label}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
  
              <Grid size={{ xs: 12 }}>
                <TextField
                  fullWidth
                  label="Notification Webhook (optional)"
                  value={config.notification_webhook}
                  onChange={handleChange('notification_webhook')}
                  disabled={startBatchMutation.isPending}
                  helperText="URL to receive notifications when batch completes"
                />
              </Grid>
  
              <Grid size={{ xs: 12 }}>
                <FormControlLabel
                  control={
                    <Checkbox
                      checked={config.retry_failed_items}
                      onChange={handleChange('retry_failed_items')}
                      disabled={startBatchMutation.isPending}
                    />
                  }
                  label="Retry failed items automatically"
                />
              </Grid>
  
              <Grid size={{ xs: 12 }}>
                <Box display="flex" gap={2} justifyContent="flex-end">
                  <Button
                    type="submit"
                    variant="contained"
                    disabled={startBatchMutation.isPending}
                    startIcon={startBatchMutation.isPending ? <CircularProgress size={20} /> : null}
                  >
                    {startBatchMutation.isPending ? 'Starting...' : 'Start Batch'}
                  </Button>
                </Box>
              </Grid>
            </Grid>
          </Box>
        </CardContent>
      </Card>
    );
  }