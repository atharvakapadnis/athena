import { Typography } from '@mui/material';
import { usePageTitle } from '@/hooks/use-page-title';

export function DashboardPage() {
    usePageTitle('Dashboard');

    return (
        <div>
            <Typography variant="h4" component="h1" gutterBottom>
                Dashboard
            </Typography>
            <Typography variant="body1">
                Welcome to the Athena Smart Description System Dashboard.
            </Typography>
        </div>
    );
}