import React from 'react';
import { Grid, Paper, Typography, Box } from '@mui/material';
import { useQuery } from '@tanstack/react-query';
import { metricsApi } from '@api/client';
import { GpuMetrics } from './components/GpuMetrics';
import { ModelList } from './components/ModelList';
import { SystemMetrics } from './components/SystemMetrics';
import { RecentActivity } from './components/RecentActivity';

export const Dashboard: React.FC = () => {
  const { data: gpuMetrics, isLoading: isLoadingGpu } = useQuery(
    ['gpuMetrics'],
    metricsApi.getGpuMetrics,
    {
      refetchInterval: 5000,
    }
  );

  const { data: systemMetrics, isLoading: isLoadingSystem } = useQuery(
    ['systemMetrics'],
    metricsApi.getSystemMetrics,
    {
      refetchInterval: 5000,
    }
  );

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <GpuMetrics data={gpuMetrics} isLoading={isLoadingGpu} />
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <SystemMetrics data={systemMetrics} isLoading={isLoadingSystem} />
          </Paper>
        </Grid>
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <ModelList />
          </Paper>
        </Grid>
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <RecentActivity />
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}; 