import React, { useState } from 'react';
import {
    AppBar,
    Toolbar,
    Typography,
    Box,
    IconButton,
    Menu,
    MenuItem,
    Avatar,
    Chip,
} from '@mui/material';
import {
    AccountCircle,
    ExitToApp as LogoutIcon,
} from '@mui/icons-material';
import { useAuth } from '@/hooks/use-auth';

const DRAWER_WIDTH = 240;

export function Header() {
    const { user, logout } = useAuth();
    const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

    const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
        setAnchorEl(event.currentTarget);
    };

    const handleMenuClose = () => {
        setAnchorEl(null);
    };

    const handleLogout = () => {
        logout();
        handleMenuClose();
    };

    return (
        <AppBar
          position="fixed"
          sx={{
            width: `calc(100% - ${DRAWER_WIDTH}px)`,
            ml: `${DRAWER_WIDTH}px`,
          }}
        >
          <Toolbar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
              {/* Page title will be set by individual pages */}
            </Typography>
    
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              {user && (
                <Chip
                  label={user.role}
                  size="small"
                  color={user.role === 'admin' ? 'secondary' : 'default'}
                  variant="outlined"
                  sx={{ color: 'white', borderColor: 'white' }}
                />
              )}
    
              <IconButton
                size="large"
                edge="end"
                aria-label="account of current user"
                aria-controls="user-menu"
                aria-haspopup="true"
                onClick={handleMenuOpen}
                color="inherit"
              >
                <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.dark' }}>
                  {user?.username?.[0]?.toUpperCase() || <AccountCircle />}
                </Avatar>
              </IconButton>
    
              <Menu
                id="user-menu"
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleMenuClose}
                transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
              >
                <MenuItem disabled>
                  <Box>
                    <Typography variant="subtitle2">{user?.username}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {user?.email}
                    </Typography>
                  </Box>
                </MenuItem>
                <MenuItem onClick={handleLogout}>
                  <LogoutIcon sx={{ mr: 1 }} />
                  Logout
                </MenuItem>
              </Menu>
            </Box>
          </Toolbar>
        </AppBar>
      );
}