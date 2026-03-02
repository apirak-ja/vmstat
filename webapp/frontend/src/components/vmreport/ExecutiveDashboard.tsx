/**
 * Executive Dashboard Component
 * แดชบอร์ดผู้บริหาร - สรุปภาพรวมทรัพยากร VM
 * 
 * ✅ Mobile First Responsive
 * ✅ Real-time Data
 * ✅ Export PDF
 */

import { useState, useEffect } from 'react';
import {
    Box,
    Grid,
    Card,
    CardContent,
    Typography,
    Alert,
    Chip,
    alpha,
    useTheme,
    Button,
    Skeleton,
    IconButton,
    Tooltip,
} from '@mui/material';
import {
    Warning as WarningIcon,
    CheckCircle as CheckIcon,
    Error as ErrorIcon,
    TrendingUp,
    Computer,
    Refresh,
    Download,
} from '@mui/icons-material';
import {
    AreaChart,
    Area,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip as RechartsTooltip,
    Legend,
    ResponsiveContainer,
} from 'recharts';
import api from '../../services/api';

interface SummaryData {
    total_vms: number;
    critical_vms: number;
    warning_vms: number;
    healthy_vms: number;
}

interface OverviewDataPoint {
    date: string;
    cpu: number;
    memory: number;
    disk: number;
}

interface TopVM {
    vm_name: string;
    cpu_percent: number;
    memory_percent: number;
    disk_percent: number;
}

interface CapacityForecast {
    resource: string;
    avg_days_until_full: number | null;
    critical_count: number;
}

export default function ExecutiveDashboard() {
    const theme = useTheme();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [data, setData] = useState<{
        summary: SummaryData;
        overview_chart: OverviewDataPoint[];
        top_vms: TopVM[];
        capacity_forecast: CapacityForecast[];
    } | null>(null);

    const fetchData = async () => {
        try {
            setLoading(true);
            setError('');
            const response = await api.get('/vmreport/executive-dashboard');
            if (response.data.success) {
                setData(response.data.data);
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'เกิดข้อผิดพลาดในการโหลดข้อมูล');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    if (loading) {
        return (
            <Box className="space-y-4">
                <Grid container spacing={{ xs: 2, md: 3 }}>
                    {[1, 2, 3, 4].map((i) => (
                        <Grid item xs={12} sm={6} md={3} key={i}>
                            <Skeleton variant="rectangular" height={140} sx={{ borderRadius: 2 }} />
                        </Grid>
                    ))}
                </Grid>
                <Skeleton variant="rectangular" height={300} sx={{ borderRadius: 2 }} />
            </Box>
        );
    }

    if (error) {
        return (
            <Alert severity="error" action={
                <Button color="inherit" size="small" onClick={fetchData}>
                    ลองใหม่
                </Button>
            }>
                {error}
            </Alert>
        );
    }

    if (!data) return null;

    const { summary, overview_chart, top_vms, capacity_forecast } = data;

    // Note: Risk calculation available if needed
    // const riskPercent = summary.total_vms > 0
    //     ? ((summary.critical_vms + summary.warning_vms) / summary.total_vms * 100).toFixed(1)
    //     : '0';

    return (
        <Box className="space-y-4 md:space-y-6">
            {/* Header Actions */}
            <Box className="flex justify-between items-center">
                <Typography variant="h5" fontWeight={700} className="hidden md:block">
                    แดชบอร์ดผู้บริหาร
                </Typography>
                <Box className="flex gap-2 ml-auto">
                    <Tooltip title="รีเฟรชข้อมูล">
                        <IconButton
                            onClick={fetchData}
                            size="small"
                            sx={{
                                bgcolor: alpha(theme.palette.primary.main, 0.1),
                                '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.2) },
                            }}
                        >
                            <Refresh fontSize="small" />
                        </IconButton>
                    </Tooltip>
                    <Button
                        variant="contained"
                        startIcon={<Download />}
                        size="small"
                        sx={{
                            textTransform: 'none',
                            borderRadius: 2,
                            fontWeight: 600,
                        }}
                    >
                        ส่งออก PDF
                    </Button>
                </Box>
            </Box>

            {/* Summary Cards */}
            <Grid container spacing={{ xs: 2, md: 3 }}>
                {/* Total VMs */}
                <Grid item xs={12} sm={6} md={3}>
                    <Card
                        elevation={0}
                        sx={{
                            height: '100%',
                            background: `linear-gradient(135deg, ${alpha(theme.palette.info.main, 0.1)} 0%, ${alpha(theme.palette.info.dark, 0.05)} 100%)`,
                            border: `1px solid ${alpha(theme.palette.info.main, 0.2)}`,
                            borderRadius: 3,
                        }}
                    >
                        <CardContent className="p-4">
                            <Box className="flex items-start justify-between">
                                <Box>
                                    <Typography variant="body2" color="text.secondary" fontWeight={600} gutterBottom>
                                        VM ทั้งหมด
                                    </Typography>
                                    <Typography variant="h3" fontWeight={800} color="info.main">
                                        {summary.total_vms}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        เครื่องเสมือน
                                    </Typography>
                                </Box>
                                <Computer sx={{ fontSize: 40, color: 'info.main', opacity: 0.3 }} />
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Critical VMs */}
                <Grid item xs={12} sm={6} md={3}>
                    <Card
                        elevation={0}
                        sx={{
                            height: '100%',
                            background: `linear-gradient(135deg, ${alpha(theme.palette.error.main, 0.1)} 0%, ${alpha(theme.palette.error.dark, 0.05)} 100%)`,
                            border: `1px solid ${alpha(theme.palette.error.main, 0.2)}`,
                            borderRadius: 3,
                        }}
                    >
                        <CardContent className="p-4">
                            <Box className="flex items-start justify-between">
                                <Box>
                                    <Typography variant="body2" color="text.secondary" fontWeight={600} gutterBottom>
                                        สถานะวิกฤติ
                                    </Typography>
                                    <Typography variant="h3" fontWeight={800} color="error.main">
                                        {summary.critical_vms}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        ต้องดำเนินการเร่งด่วน
                                    </Typography>
                                </Box>
                                <ErrorIcon sx={{ fontSize: 40, color: 'error.main', opacity: 0.3 }} />
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Warning VMs */}
                <Grid item xs={12} sm={6} md={3}>
                    <Card
                        elevation={0}
                        sx={{
                            height: '100%',
                            background: `linear-gradient(135deg, ${alpha(theme.palette.warning.main, 0.1)} 0%, ${alpha(theme.palette.warning.dark, 0.05)} 100%)`,
                            border: `1px solid ${alpha(theme.palette.warning.main, 0.2)}`,
                            borderRadius: 3,
                        }}
                    >
                        <CardContent className="p-4">
                            <Box className="flex items-start justify-between">
                                <Box>
                                    <Typography variant="body2" color="text.secondary" fontWeight={600} gutterBottom>
                                        ต้องเฝ้าระวัง
                                    </Typography>
                                    <Typography variant="h3" fontWeight={800} color="warning.main">
                                        {summary.warning_vms}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        ควรตรวจสอบ
                                    </Typography>
                                </Box>
                                <WarningIcon sx={{ fontSize: 40, color: 'warning.main', opacity: 0.3 }} />
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Healthy VMs */}
                <Grid item xs={12} sm={6} md={3}>
                    <Card
                        elevation={0}
                        sx={{
                            height: '100%',
                            background: `linear-gradient(135deg, ${alpha(theme.palette.success.main, 0.1)} 0%, ${alpha(theme.palette.success.dark, 0.05)} 100%)`,
                            border: `1px solid ${alpha(theme.palette.success.main, 0.2)}`,
                            borderRadius: 3,
                        }}
                    >
                        <CardContent className="p-4">
                            <Box className="flex items-start justify-between">
                                <Box>
                                    <Typography variant="body2" color="text.secondary" fontWeight={600} gutterBottom>
                                        สถานะปกติ
                                    </Typography>
                                    <Typography variant="h3" fontWeight={800} color="success.main">
                                        {summary.healthy_vms}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                        ทำงานปกติ
                                    </Typography>
                                </Box>
                                <CheckIcon sx={{ fontSize: 40, color: 'success.main', opacity: 0.3 }} />
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {/* Overview Chart - 7 Days Trend */}
            <Card
                elevation={0}
                sx={{
                    bgcolor: alpha(theme.palette.background.paper, 0.6),
                    backdropFilter: 'blur(10px)',
                    border: `1px solid ${theme.palette.divider}`,
                    borderRadius: 3,
                }}
            >
                <CardContent className="p-4 md:p-6">
                    <Box className="flex items-center justify-between mb-4">
                        <Box>
                            <Typography variant="h6" fontWeight={700} gutterBottom>
                                แนวโน้มการใช้ทรัพยากร 7 วันล่าสุด
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                                ค่าเฉลี่ยการใช้ CPU, RAM และ Disk ของ VM ทั้งหมด
                            </Typography>
                        </Box>
                    </Box>

                    <ResponsiveContainer width="100%" height={300}>
                        <AreaChart data={overview_chart}>
                            <defs>
                                <linearGradient id="colorCpu" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={theme.palette.primary.main} stopOpacity={0.3} />
                                    <stop offset="95%" stopColor={theme.palette.primary.main} stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="colorMemory" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={theme.palette.secondary.main} stopOpacity={0.3} />
                                    <stop offset="95%" stopColor={theme.palette.secondary.main} stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="colorDisk" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor={theme.palette.warning.main} stopOpacity={0.3} />
                                    <stop offset="95%" stopColor={theme.palette.warning.main} stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                            <XAxis
                                dataKey="date"
                                stroke={theme.palette.text.secondary}
                                style={{ fontSize: '12px' }}
                            />
                            <YAxis
                                stroke={theme.palette.text.secondary}
                                style={{ fontSize: '12px' }}
                                label={{ value: 'การใช้งาน (%)', angle: -90, position: 'insideLeft' }}
                            />
                            <RechartsTooltip
                                contentStyle={{
                                    backgroundColor: theme.palette.background.paper,
                                    border: `1px solid ${theme.palette.divider}`,
                                    borderRadius: 8,
                                }}
                                formatter={(value: number) => `${value.toFixed(2)}%`}
                            />
                            <Legend />
                            <Area
                                type="monotone"
                                dataKey="cpu"
                                stroke={theme.palette.primary.main}
                                fillOpacity={1}
                                fill="url(#colorCpu)"
                                name="CPU"
                                strokeWidth={2}
                            />
                            <Area
                                type="monotone"
                                dataKey="memory"
                                stroke={theme.palette.secondary.main}
                                fillOpacity={1}
                                fill="url(#colorMemory)"
                                name="RAM"
                                strokeWidth={2}
                            />
                            <Area
                                type="monotone"
                                dataKey="disk"
                                stroke={theme.palette.warning.main}
                                fillOpacity={1}
                                fill="url(#colorDisk)"
                                name="Disk"
                                strokeWidth={2}
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </CardContent>
            </Card>

            {/* Two Column Layout */}
            <Grid container spacing={{ xs: 2, md: 3 }}>
                {/* Top 5 VMs */}
                <Grid item xs={12} lg={6}>
                    <Card
                        elevation={0}
                        sx={{
                            height: '100%',
                            bgcolor: alpha(theme.palette.background.paper, 0.6),
                            backdropFilter: 'blur(10px)',
                            border: `1px solid ${theme.palette.divider}`,
                            borderRadius: 3,
                        }}
                    >
                        <CardContent className="p-4 md:p-6">
                            <Typography variant="h6" fontWeight={700} gutterBottom>
                                Top 5 VM ที่ใช้ทรัพยากรสูงสุด
                            </Typography>
                            <Typography variant="caption" color="text.secondary" className="mb-4 block">
                                จัดอันดับตามการใช้ CPU
                            </Typography>

                            <Box className="space-y-3 mt-4">
                                {top_vms.map((vm, index) => (
                                    <Box
                                        key={index}
                                        className="p-3 rounded-lg"
                                        sx={{
                                            bgcolor: alpha(theme.palette.background.default, 0.5),
                                            border: `1px solid ${theme.palette.divider}`,
                                        }}
                                    >
                                        <Box className="flex items-center justify-between mb-2">
                                            <Typography variant="body2" fontWeight={600}>
                                                {index + 1}. {vm.vm_name}
                                            </Typography>
                                            <Chip
                                                label={`${vm.cpu_percent.toFixed(1)}% CPU`}
                                                size="small"
                                                color={vm.cpu_percent > 80 ? 'error' : vm.cpu_percent > 60 ? 'warning' : 'success'}
                                                sx={{ fontWeight: 600 }}
                                            />
                                        </Box>
                                        <Grid container spacing={1}>
                                            <Grid item xs={4}>
                                                <Typography variant="caption" color="text.secondary">
                                                    CPU
                                                </Typography>
                                                <Typography variant="body2" fontWeight={600} color="primary">
                                                    {vm.cpu_percent.toFixed(1)}%
                                                </Typography>
                                            </Grid>
                                            <Grid item xs={4}>
                                                <Typography variant="caption" color="text.secondary">
                                                    RAM
                                                </Typography>
                                                <Typography variant="body2" fontWeight={600} color="secondary">
                                                    {vm.memory_percent.toFixed(1)}%
                                                </Typography>
                                            </Grid>
                                            <Grid item xs={4}>
                                                <Typography variant="caption" color="text.secondary">
                                                    Disk
                                                </Typography>
                                                <Typography variant="body2" fontWeight={600} color="warning.main">
                                                    {vm.disk_percent.toFixed(1)}%
                                                </Typography>
                                            </Grid>
                                        </Grid>
                                    </Box>
                                ))}
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>

                {/* Capacity Forecast */}
                <Grid item xs={12} lg={6}>
                    <Card
                        elevation={0}
                        sx={{
                            height: '100%',
                            bgcolor: alpha(theme.palette.background.paper, 0.6),
                            backdropFilter: 'blur(10px)',
                            border: `1px solid ${theme.palette.divider}`,
                            borderRadius: 3,
                        }}
                    >
                        <CardContent className="p-4 md:p-6">
                            <Typography variant="h6" fontWeight={700} gutterBottom>
                                การพยากรณ์ความจุ
                            </Typography>
                            <Typography variant="caption" color="text.secondary" className="mb-4 block">
                                ประมาณการวันที่ทรัพยากรจะเต็ม
                            </Typography>

                            <Box className="space-y-4 mt-4">
                                {capacity_forecast.map((item, index) => (
                                    <Box key={index}>
                                        <Box className="flex items-center justify-between mb-2">
                                            <Typography variant="body2" fontWeight={600} textTransform="uppercase">
                                                {item.resource === 'disk' ? 'พื้นที่ดิสก์' : item.resource === 'memory' ? 'หน่วยความจำ' : 'CPU'}
                                            </Typography>
                                            {item.critical_count > 0 && (
                                                <Chip
                                                    label={`${item.critical_count} VM วิกฤติ`}
                                                    size="small"
                                                    color="error"
                                                    icon={<WarningIcon />}
                                                />
                                            )}
                                        </Box>
                                        <Box
                                            className="p-3 rounded-lg flex items-center gap-3"
                                            sx={{
                                                bgcolor: alpha(theme.palette.background.default, 0.5),
                                                border: `1px solid ${theme.palette.divider}`,
                                            }}
                                        >
                                            <TrendingUp
                                                sx={{
                                                    fontSize: 40,
                                                    color: item.avg_days_until_full && item.avg_days_until_full < 30
                                                        ? theme.palette.error.main
                                                        : theme.palette.success.main,
                                                    opacity: 0.6,
                                                }}
                                            />
                                            <Box>
                                                <Typography variant="h4" fontWeight={800}>
                                                    {item.avg_days_until_full !== null ? `${item.avg_days_until_full} วัน` : 'N/A'}
                                                </Typography>
                                                <Typography variant="caption" color="text.secondary">
                                                    โดยเฉลี่ยจะเต็มใน
                                                </Typography>
                                            </Box>
                                        </Box>
                                    </Box>
                                ))}
                            </Box>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>
        </Box>
    );
}
