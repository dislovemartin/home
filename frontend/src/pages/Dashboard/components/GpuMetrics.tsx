import React from 'react';
import { Box, Typography, LinearProgress, Grid, Skeleton } from '@mui/material';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface GpuMetric {
  timestamp: string;
  gpu_id: string;
  utilization: number;
  memory_used: number;
  memory_total: number;
  temperature: number;
  power_usage: number;
}

interface Props {
  data?: GpuMetric[];
  isLoading: boolean;
}

export const GpuMetrics: React.FC<Props> = ({ data, isLoading }) => {
  if (isLoading) {
    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          GPU Metrics
        </Typography>
        <Skeleton variant="rectangular" height={200} />
      </Box>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Box>
        <Typography variant="h6" gutterBottom>
          GPU Metrics
        </Typography>
        <Typography color="textSecondary">No GPU data available</Typography>
      </Box>
    );
  }

  const latestMetrics = data[data.length - 1];
  const timestamps = data.map((d) => new Date(d.timestamp).toLocaleTimeString());
  const utilizationData = data.map((d) => d.utilization);
  const memoryUsageData = data.map((d) => (d.memory_used / d.memory_total) * 100);

  const chartData = {
    labels: timestamps,
    datasets: [
      {
        label: 'GPU Utilization (%)',
        data: utilizationData,
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.1,
      },
      {
        label: 'Memory Usage (%)',
        data: memoryUsageData,
        borderColor: 'rgb(255, 99, 132)',
        tension: 0.1,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: false,
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
      },
    },
  };

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        GPU Metrics
      </Typography>
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={6} md={3}>
          <Typography variant="body2" color="textSecondary">
            Utilization
          </Typography>
          <LinearProgress
            variant="determinate"
            value={latestMetrics.utilization}
            sx={{ height: 10, borderRadius: 5 }}
          />
          <Typography variant="body2">{latestMetrics.utilization}%</Typography>
        </Grid>
        <Grid item xs={6} md={3}>
          <Typography variant="body2" color="textSecondary">
            Memory Usage
          </Typography>
          <LinearProgress
            variant="determinate"
            value={(latestMetrics.memory_used / latestMetrics.memory_total) * 100}
            sx={{ height: 10, borderRadius: 5 }}
          />
          <Typography variant="body2">
            {Math.round((latestMetrics.memory_used / latestMetrics.memory_total) * 100)}%
          </Typography>
        </Grid>
        <Grid item xs={6} md={3}>
          <Typography variant="body2" color="textSecondary">
            Temperature
          </Typography>
          <Typography variant="h6">{latestMetrics.temperature}°C</Typography>
        </Grid>
        <Grid item xs={6} md={3}>
          <Typography variant="body2" color="textSecondary">
            Power Usage
          </Typography>
          <Typography variant="h6">{latestMetrics.power_usage}W</Typography>
        </Grid>
      </Grid>
      <Box sx={{ height: 300 }}>
        <Line data={chartData} options={chartOptions} />
      </Box>
    </Box>
  );
}; 