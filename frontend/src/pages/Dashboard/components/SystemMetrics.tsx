import React from 'react';
import { Box, Typography, CircularProgress, Grid, Skeleton } from '@mui/material';

interface SystemMetric {
  cpu_usage: number;
  memory_used: number;
  memory_total: number;
  disk_used: number;
  disk_total: number;
  network_rx: number;
  network_tx: number;
}

interface Props {
  data?: SystemMetric;
  isLoading: boolean;
}

export const SystemMetrics: React.FC<Props> = ({ data, isLoading }) => {
  if (isLoading) {
    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          System Metrics
        </Typography>
        <Skeleton variant="rectangular" height={200} />
      </Box>
    );
  }

  if (!data) {
    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          System Metrics
        </Typography>
        <Typography color="textSecondary">No system data available</Typography>
      </Box>
    );
  }

  const formatBytes = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        System Metrics
      </Typography>
      <Grid container spacing={2}>
        <Grid item xs={6}>
          <Box sx={{ position: 'relative', display: 'inline-flex' }}>
            <CircularProgress
              variant="determinate"
              value={data.cpu_usage}
              size={80}
              thickness={4}
            />
            <Box
              sx={{
                top: 0,
                left: 0,
                bottom: 0,
                right: 0,
                position: 'absolute',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Typography variant="caption" component="div" color="text.secondary">
                {`${Math.round(data.cpu_usage)}%`}
              </Typography>
            </Box>
          </Box>
          <Typography variant="body2" color="textSecondary" align="center">
            CPU Usage
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Box sx={{ position: 'relative', display: 'inline-flex' }}>
            <CircularProgress
              variant="determinate"
              value={(data.memory_used / data.memory_total) * 100}
              size={80}
              thickness={4}
            />
            <Box
              sx={{
                top: 0,
                left: 0,
                bottom: 0,
                right: 0,
                position: 'absolute',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Typography variant="caption" component="div" color="text.secondary">
                {`${Math.round((data.memory_used / data.memory_total) * 100)}%`}
              </Typography>
            </Box>
          </Box>
          <Typography variant="body2" color="textSecondary" align="center">
            Memory Usage
          </Typography>
        </Grid>
        <Grid item xs={12}>
          <Typography variant="body2" color="textSecondary">
            Disk Usage
          </Typography>
          <Typography variant="body1">
            {formatBytes(data.disk_used)} / {formatBytes(data.disk_total)}
          </Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="textSecondary">
            Network RX
          </Typography>
          <Typography variant="body1">{formatBytes(data.network_rx)}/s</Typography>
        </Grid>
        <Grid item xs={6}>
          <Typography variant="body2" color="textSecondary">
            Network TX
          </Typography>
          <Typography variant="body1">{formatBytes(data.network_tx)}/s</Typography>
        </Grid>
      </Grid>
    </Box>
  );
}; 