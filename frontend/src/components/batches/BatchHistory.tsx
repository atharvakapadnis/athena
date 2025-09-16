import { useState } from 'react';
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
    Box,
    Pagination,
    IconButton,
    Tooltip
} from '@mui/material';

import { Visibility as ViewIcon } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { batchService } from '@/services/api';
import { QUERY_KEYS } from '@/constants';
import { BATCH_STATUS_COLORS } from '@/constants/batch-config';
import type { Batch } from '@/types';

export function BatchHistory() {
    const [page, setPage] = useState(1);
    const [perPage] = useState(20);
    const navigate = useNavigate();

    const {
        data: historyData,
        isLoading,
        error,
    } = useQuery({
        queryKey: [...QUERY_KEYS.BATCH_HISTORY, page, perPage],
        queryFn: () => batchService.getHistory(page, perPage),
    });

    const handleViewBatch = (batchId: string) => {
        navigate(`/batches/${batchId}`);
    };

    const handlePageChange = (_: React.ChangeEvent<unknown>, newPage: number) => {
        setPage(newPage);
    };

    const formatDateTime = (dateString?: string) => {
        return dateString ? new Date(dateString).toLocaleString() : 'N/A';
    };

    const formatDuration = (startTime?: string, endTime?: string) => {
        if(!startTime || !endTime) return 'N/A';
        const duration = new Date(endTime).getTime() - new Date(startTime).getTime();
        const minutes = Math.floor(duration / 60000);
        const seconds = Math.floor((duration % 60000) / 1000);
        return `${minutes}m ${seconds}s`;
    };

    const getStatusColor = (status: Batch['status']) => {
        return BATCH_STATUS_COLORS[status] as any;
    };

    if (isLoading) {
        return (
            <Card>
                <CardContent>
                    <Typography color="error">
                        Error loadin batch history: {(error as any)?.message || 'Unknown error'}
                    </Typography>
                </CardContent>
            </Card>
        );
    }

    if (error){
        return (
            <Card>
                <CardContent>
                    <Typography color="error">
                        Error loading batch history: {(error as any)?.message || 'Unknown error'}
                    </Typography>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Batch History
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Total: {historyData?.total || 0} batches
              </Typography>
            </Box>
    
            {!historyData || historyData.items.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                No batch history found.
              </Typography>
            ) : (
              <>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Batch ID</TableCell>
                        <TableCell>Status</TableCell>
                        <TableCell>Items</TableCell>
                        <TableCell>Success Rate</TableCell>
                        <TableCell>Duration</TableCell>
                        <TableCell>Created</TableCell>
                        <TableCell align="center">Actions</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {historyData.items.map((batch) => (
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
                            <Typography variant="body2">
                              {batch.processed_items}/{batch.total_items}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              ({batch.progress.toFixed(1)}%)
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {batch.processed_items > 0 
                                ? `${((batch.success_count / batch.processed_items) * 100).toFixed(1)}%`
                                : 'N/A'
                              }
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {batch.success_count}✓ {batch.error_count}✗
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {formatDuration(batch.started_at, batch.completed_at)}
                            </Typography>
                          </TableCell>
                          <TableCell>
                            <Typography variant="body2">
                              {formatDateTime(batch.created_at)}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              by {batch.created_by}
                            </Typography>
                          </TableCell>
                          <TableCell align="center">
                            <Tooltip title="View Details">
                              <IconButton
                                size="small"
                                onClick={() => handleViewBatch(batch.id)}
                              >
                                <ViewIcon />
                              </IconButton>
                            </Tooltip>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
    
                {historyData.total_pages > 1 && (
                  <Box display="flex" justifyContent="center" mt={3}>
                    <Pagination
                      count={historyData.total_pages}
                      page={page}
                      onChange={handlePageChange}
                      color="primary"
                    />
                  </Box>
                )}
              </>
            )}
          </CardContent>
        </Card>
    );
}