import {
    Card,
    CardContent,
    Typography,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Chip,
    Button,
    LinearProgress,
    Box,
    IconButton,
    Tooltip,
  } from '@mui/material';
  import {
    Pause as PauseIcon,
    PlayArrow as ResumeIcon,
    Stop as CancelIcon,
    Visibility as ViewIcon,
  } from '@mui/icons-material';
  import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
  import { useNavigate } from 'react-router-dom';
  import { batchService } from '@/services/api';
  import { QUERY_KEYS } from '@/constants';
  import { BATCH_STATUS_COLORS } from '@/constants/batch-config';
  import type { Batch } from '@/types';
  
  export function BatchQueue() {
    const navigate = useNavigate();
    const queryClient = useQueryClient();
  
    const {
      data: batches,
      isLoading,
      error,
    } = useQuery({
      queryKey: QUERY_KEYS.BATCH_QUEUE,
      queryFn: batchService.getQueue,
      refetchInterval: 30000, // Poll every 30 seconds
      staleTime: 15000, // Consider data stale after 15 seconds
    });
  
    const pauseBatchMutation = useMutation({
      mutationFn: batchService.pauseBatch,
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.BATCH_QUEUE });
      },
    });
  
    const resumeBatchMutation = useMutation({
      mutationFn: batchService.resumeBatch,
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.BATCH_QUEUE });
      },
    });
  
    const cancelBatchMutation = useMutation({
      mutationFn: batchService.cancelBatch,
      onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: QUERY_KEYS.BATCH_QUEUE });
      },
    });
  
    const handleViewBatch = (batchId: string) => {
      navigate(`/batches/${batchId}`);
    };
  
    const formatDateTime = (dateString: string) => {
      return new Date(dateString).toLocaleString();
    };
  
    const getStatusColor = (status: Batch['status']) => {
      return BATCH_STATUS_COLORS[status] as any;
    };
  
    if (isLoading) {
      return (
        <Card>
          <CardContent>
            <Typography>Loading batch queue...</Typography>
          </CardContent>
        </Card>
      );
    }
  
    if (error) {
      return (
        <Card>
          <CardContent>
            <Typography color="error">
              Error loading batch queue: {(error as any)?.message || 'Unknown error'}
            </Typography>
          </CardContent>
        </Card>
      );
    }
  
    return (
      <Card>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Active Batch Queue
          </Typography>
  
          {!batches || batches.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              No active batches in queue.
            </Typography>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Batch ID</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Progress</TableCell>
                    <TableCell>Created</TableCell>
                    <TableCell>Priority</TableCell>
                    <TableCell align="center">Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {batches.map((batch) => (
                    <TableRow key={batch.id}>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {batch.id.substring(0, 8)}...
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={batch.status}
                          color={getStatusColor(batch.status)}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Box width={120}>
                          <LinearProgress
                            variant="determinate"
                            value={batch.progress}
                            sx={{ mb: 0.5 }}
                          />
                          <Typography variant="caption">
                            {batch.processed_items}/{batch.total_items} ({batch.progress.toFixed(1)}%)
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {formatDateTime(batch.created_at)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          by {batch.created_by}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={batch.config.priority}
                          variant="outlined"
                          size="small"
                          color={
                            batch.config.priority === 'high' ? 'error' :
                            batch.config.priority === 'low' ? 'secondary' : 'primary'
                          }
                        />
                      </TableCell>
                      <TableCell align="center">
                        <Box display="flex" gap={0.5}>
                          <Tooltip title="View Details">
                            <IconButton
                              size="small"
                              onClick={() => handleViewBatch(batch.id)}
                            >
                              <ViewIcon />
                            </IconButton>
                          </Tooltip>
  
                          {batch.status === 'running' && (
                            <Tooltip title="Pause Batch">
                              <IconButton
                                size="small"
                                onClick={() => pauseBatchMutation.mutate(batch.id)}
                                disabled={pauseBatchMutation.isPending}
                              >
                                <PauseIcon />
                              </IconButton>
                            </Tooltip>
                          )}
  
                          {batch.status === 'paused' && (
                            <Tooltip title="Resume Batch">
                              <IconButton
                                size="small"
                                onClick={() => resumeBatchMutation.mutate(batch.id)}
                                disabled={resumeBatchMutation.isPending}
                              >
                                <ResumeIcon />
                              </IconButton>
                            </Tooltip>
                          )}
  
                          {(['running', 'paused', 'pending'].includes(batch.status)) && (
                            <Tooltip title="Cancel Batch">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={() => cancelBatchMutation.mutate(batch.id)}
                                disabled={cancelBatchMutation.isPending}
                              >
                                <CancelIcon />
                              </IconButton>
                            </Tooltip>
                          )}
                        </Box>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </CardContent>
      </Card>
    );
  }