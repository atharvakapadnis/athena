import { Box, Toolbar } from '@mui/material';
import { Sidebar } from './Sidebar';
import { Header } from './Header';

interface AppLayoutProps {
    children: React.ReactNode;
}

const DRAWER_WIDTH = 240;

export function AppLayout({ children }: AppLayoutProps) {
    return (
        <Box sx={{ display: 'flex' }}>
            <Header />
            <Sidebar />
            <Box
            component="main"
            sx={{
                flexGrow: 1,
                bgcolor: 'background.default',
                ml: `${DRAWER_WIDTH}px`,
                minHeight: '100vh',
            }}
            >
                <Toolbar /> {/*This create space for the fixed header*/}
                <Box sx={{ p: 3 }}>
                    {children}
                </Box>
            </Box>
        </Box>
    );
}