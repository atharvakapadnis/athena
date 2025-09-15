import { useLocation, useNavigate } from 'react-router-dom';
import {
    Drawer,
    List,
    ListItem,
    ListItemButton,
    ListItemIcon,
    ListItemText,
    Typography,
    Box,
    Divider,
} from '@mui/material';
import {
    Dashboard as DashboardIcon,
    PlayArrow as BatchIcon,
    Rule as RuleIcon,
    Psychology as AIIcon,
    Settings as SystemIcon,
} from '@mui/icons-material';
import { ROUTES } from '@/constants';

const DRAWER_WIDTH = 240;

const menuItems = [
    {
        text: 'Dashboard',
        icon: <DashboardIcon />,
        path: ROUTES.DASHBOARD,
    },
    {
        text: 'Batch Management',
        icon: <BatchIcon />,
        path: ROUTES.BATCHES,
    },
    {
        text: 'Rule Management',
        icon: <RuleIcon />,
        path: ROUTES.RULES,
    },
    {
        text: 'AI Analysis',
        icon: <AIIcon />,
        path: ROUTES.AI_ANALYSIS,
    },
    {
        text: 'System Admin',
        icon: <SystemIcon />,
        path: ROUTES.SYSTEM,
    },
];

export function Sidebar() {
    const location = useLocation();
    const navigate = useNavigate();

    const handleNavigate = (path: string) => {
        navigate(path);
    };

    return (
        <Drawer
          variant="permanent"
          sx={{
            width: DRAWER_WIDTH,
            flexShrink: 0,
            '& .MuiDrawer-paper': {
              width: DRAWER_WIDTH,
              boxSizing: 'border-box',
            },
          }}
        >
          <Box sx={{ p: 2 }}>
            <Typography variant="h6" component="h1" sx={{ fontWeight: 'bold' }}>
              Athena System
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Smart Description Management
            </Typography>
          </Box>
          
          <Divider />
          
          <List>
            {menuItems.map((item) => (
              <ListItem key={item.path} disablePadding>
                <ListItemButton
                  selected={location.pathname === item.path}
                  onClick={() => handleNavigate(item.path)}
                  sx={{
                    '&.Mui-selected': {
                      backgroundColor: 'primary.main',
                      color: 'primary.contrastText',
                      '&:hover': {
                        backgroundColor: 'primary.dark',
                      },
                      '& .MuiListItemIcon-root': {
                        color: 'primary.contrastText',
                      },
                    },
                  }}
                >
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Drawer>
    );
}