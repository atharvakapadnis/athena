import React, { useState } from 'react';
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
  Box,
  Pagination,
  IconButton,
  Tooltip,
  Alert,
} from '@mui/material';
import { Visibility as ViewIcon, Refresh as RefreshIcon } from '@mui/icons-material';
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
    refetch,
  } = useQuery({
    queryKey: [...QUERY_KEYS.BATCH_HISTORY, page, perPage],
    queryFn: () => batchService.getHistory(page, perPage),
    retry: 1,
  });

  const handleViewBatch = (batchId: string) => {
    navigate(`/batches/${batchId}`);
  };

  const handlePageChange = (_: React.ChangeEvent<unknown>, newPage: number) => {
    setPage(newPage);
  };

  const formatDateTime = (dateString?: string) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString();
    } catch {
      return 'Invalid Date';
    }
  };

  const formatDuration = (startTime?: string, endTime?: string) => {
    if (!startTime || !endTime) return 'N/A';
    try {
      const duration = new Date(endTime).getTime() - new Date(startTime).getTime();
      if (isNaN(duration) || duration < 0) return 'N/A';
      const minutes = Math.floor(duration / 60000);
      const seconds = Math.floor((duration % 60000) / 1000);
      return `${minutes}m ${seconds}s`;
    } catch {
      return 'N/A';
    }
  };

  const safeNumber = (value: any, defaultValue: number = 0): number => {
    if (typeof value === 'number' && !isNaN(value)) return value;
    if (typeof value === 'string') {
      const parsed = parseFloat(value);
      if (!isNaN(parsed)) return parsed;
    }
    return defaultValue;
  };

  const getStatusColor = (status: Batch['status']) => {
    return BATCH_STATUS_COLORS[status] as any;
  };

  if (isLoading) {
    return (
      <Card>
        <CardContent>
          <Typography>Loading batch history...</Typography>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6" color="error">
              Error Loading Batch History
            </Typography>
            <IconButton onClick={() => refetch()} size="small">
              <RefreshIcon />
            </IconButton>
          </Box>
          <Alert severity="error">
            {(error as any)?.message || 'Unknown error occurred'}
          </Alert>
          <Typography variant="body2" sx={{ mt: 2 }}>
            This might be due to corrupted data in the backend. Check the server logs for details.
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
          <Box display="flex" alignItems="center" gap={1}>
            <Typography variant="body2" color="text.secondary">
              Total: {historyData?.total || 0} batches
            </Typography>
            <IconButton onClick={() => refetch()} size="small">
              <RefreshIcon />
            </IconButton>
          </Box>
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
                  {historyData.items.map((batch) => {
                    // Safe access to potentially null/undefined values
                    const processedItems = safeNumber(batch.processed_items);
                    const totalItems = safeNumber(batch.total_items);
                    const successCount = safeNumber(batch.success_count);
                    const errorCount = safeNumber(batch.error_count);
                    const progress = safeNumber(batch.progress);

                    const successRate = processedItems > 0 
                      ? ((successCount / processedItems) * 100).toFixed(1)
                      : 'N/A';

                    return (
                      <TableRow key={batch.id}>
                        <TableCell>
                          <Typography variant="body2" fontFamily="monospace">
                            {batch.id?.substring(0, 8) || 'Unknown'}...
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            label={batch.status || 'unknown'}
                            color={getStatusColor(batch.status)}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {processedItems}/{totalItems}
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            ({progress.toFixed(1)}%)
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {successRate}%
                          </Typography>
                          <Typography variant="caption" color="text.secondary">
                            {successCount}✓ {errorCount}✗
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
                            by {batch.created_by || 'Unknown'}
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
                    );
                  })}
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