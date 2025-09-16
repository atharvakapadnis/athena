import { useState } from 'react';
import {
    Typography,
    Box,
    Tabs,
    Tab,
    Paper,
  } from '@mui/material';
  import { usePageTitle } from '@/hooks/use-page-title';
  import { StartBatchForm } from '@/components/batches/StartBatchForm';
  import { BatchQueue } from '@/components/batches/BatchQueue';
  import { BatchHistory } from '@/components/batches/BatchHistory';
  
  interface TabPanelProps {
    children?: React.ReactNode;
    index: number;
    value: number;
  }
  
  function TabPanel({ children, value, index }: TabPanelProps) {
    return (
      <div hidden={value !== index} role="tabpanel">
        {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
      </div>
    );
  }
  
  export function BatchesPage() {
    usePageTitle('Batch Management');
    const [tabValue, setTabValue] = useState(0);
  
    const handleTabChange = (_: React.SyntheticEvent, newValue: number) => {
      setTabValue(newValue);
    };
  
    return (
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          Batch Management
        </Typography>
  
        <Paper sx={{ width: '100%' }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange}>
              <Tab label="Start New Batch" />
              <Tab label="Active Queue" />
              <Tab label="History" />
            </Tabs>
          </Box>
  
          <TabPanel value={tabValue} index={0}>
            <StartBatchForm 
              onSuccess={() => {
                // Switch to queue tab when batch is started successfully
                setTabValue(1);
              }}
            />
          </TabPanel>
  
          <TabPanel value={tabValue} index={1}>
            <BatchQueue />
          </TabPanel>
  
          <TabPanel value={tabValue} index={2}>
            <BatchHistory />
          </TabPanel>
        </Paper>
      </Box>
    );
  }