import React from 'react';
import {
  Box,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
} from '@mui/material';
import {
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Info as InfoIcon,
  Warning as WarningIcon,
} from '@mui/icons-material';

interface Activity {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  message: string;
  timestamp: string;
}

const mockActivities: Activity[] = [
  {
    id: '1',
    type: 'success',
    message: 'Model "bert-base" optimization completed',
    timestamp: new Date().toISOString(),
  },
  {
    id: '2',
    type: 'error',
    message: 'Failed to load model "gpt2-large"',
    timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
  },
  {
    id: '3',
    type: 'info',
    message: 'Started optimization of "roberta-base"',
    timestamp: new Date(Date.now() - 1000 * 60 * 10).toISOString(),
  },
  {
    id: '4',
    type: 'warning',
    message: 'Low disk space warning',
    timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
  },
];

const getIcon = (type: Activity['type']) => {
  switch (type) {
    case 'success':
      return <SuccessIcon color="success" />;
    case 'error':
      return <ErrorIcon color="error" />;
    case 'info':
      return <InfoIcon color="info" />;
    case 'warning':
      return <WarningIcon color="warning" />;
  }
};

const formatTimestamp = (timestamp: string) => {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 1000 / 60);

  if (minutes < 1) {
    return 'Just now';
  } else if (minutes < 60) {
    return `${minutes}m ago`;
  } else if (minutes < 1440) {
    return `${Math.floor(minutes / 60)}h ago`;
  } else {
    return date.toLocaleDateString();
  }
};

export const RecentActivity: React.FC = () => {
  return (
    <Box>
      <Typography variant="h6" gutterBottom>
        Recent Activity
      </Typography>
      <List>
        {mockActivities.map((activity, index) => (
          <React.Fragment key={activity.id}>
            <ListItem>
              <ListItemIcon>{getIcon(activity.type)}</ListItemIcon>
              <ListItemText
                primary={activity.message}
                secondary={formatTimestamp(activity.timestamp)}
              />
            </ListItem>
            {index < mockActivities.length - 1 && <Divider variant="inset" component="li" />}
          </React.Fragment>
        ))}
      </List>
    </Box>
  );
}; 