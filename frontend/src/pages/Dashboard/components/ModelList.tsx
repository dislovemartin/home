import React from 'react';
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  Chip,
  Tooltip,
  LinearProgress,
} from '@mui/material';
import {
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Delete as DeleteIcon,
  Info as InfoIcon,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { modelApi } from '@api/client';
import { useNavigate } from 'react-router-dom';

interface Model {
  id: string;
  name: string;
  status: 'ready' | 'running' | 'error' | 'stopped';
  progress: number;
  size: number;
  created_at: string;
}

export const ModelList: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data: models, isLoading } = useQuery(['models'], modelApi.list);

  const deleteMutation = useMutation(modelApi.delete, {
    onSuccess: () => {
      queryClient.invalidateQueries(['models']);
    },
  });

  const optimizeMutation = useMutation(modelApi.optimize, {
    onSuccess: () => {
      queryClient.invalidateQueries(['models']);
    },
  });

  const handleDelete = (id: string) => {
    if (window.confirm('Are you sure you want to delete this model?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleOptimize = (id: string) => {
    optimizeMutation.mutate(id);
  };

  const handleInfo = (id: string) => {
    navigate(`/models/${id}`);
  };

  const formatSize = (bytes: number) => {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(2)} ${sizes[i]}`;
  };

  const getStatusColor = (status: Model['status']) => {
    switch (status) {
      case 'ready':
        return 'success';
      case 'running':
        return 'primary';
      case 'error':
        return 'error';
      case 'stopped':
        return 'default';
      default:
        return 'default';
    }
  };

  if (isLoading) {
    return <LinearProgress />;
  }

  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Models
      </Typography>
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Name</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Progress</TableCell>
              <TableCell>Size</TableCell>
              <TableCell>Created</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {models?.map((model: Model) => (
              <TableRow key={model.id}>
                <TableCell>{model.name}</TableCell>
                <TableCell>
                  <Chip
                    label={model.status}
                    color={getStatusColor(model.status)}
                    size="small"
                  />
                </TableCell>
                <TableCell>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <Box sx={{ width: '100%', mr: 1 }}>
                      <LinearProgress
                        variant="determinate"
                        value={model.progress}
                        sx={{ height: 8, borderRadius: 4 }}
                      />
                    </Box>
                    <Box sx={{ minWidth: 35 }}>
                      <Typography variant="body2" color="text.secondary">
                        {`${Math.round(model.progress)}%`}
                      </Typography>
                    </Box>
                  </Box>
                </TableCell>
                <TableCell>{formatSize(model.size)}</TableCell>
                <TableCell>
                  {new Date(model.created_at).toLocaleDateString()}
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="View Details">
                    <IconButton
                      size="small"
                      onClick={() => handleInfo(model.id)}
                    >
                      <InfoIcon />
                    </IconButton>
                  </Tooltip>
                  {model.status === 'stopped' ? (
                    <Tooltip title="Start Optimization">
                      <IconButton
                        size="small"
                        onClick={() => handleOptimize(model.id)}
                        color="primary"
                      >
                        <PlayIcon />
                      </IconButton>
                    </Tooltip>
                  ) : model.status === 'running' ? (
                    <Tooltip title="Stop Optimization">
                      <IconButton
                        size="small"
                        onClick={() => handleOptimize(model.id)}
                        color="error"
                      >
                        <StopIcon />
                      </IconButton>
                    </Tooltip>
                  ) : null}
                  <Tooltip title="Delete Model">
                    <IconButton
                      size="small"
                      onClick={() => handleDelete(model.id)}
                      color="error"
                    >
                      <DeleteIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Box>
  );
}; 