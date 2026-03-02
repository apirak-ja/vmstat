/**
 * VM Detail Report Component
 * รายงานรายละเอียดราย VM
 * 
 * Sections:
 * 1. ข้อมูลพื้นฐาน
 * 2. Snapshot ปัจจุบัน
 * 3. กราฟย้อนหลัง
 * 4. ตารางสถิติ
 * 5. วิเคราะห์แนวโน้ม
 */

import { useState, useEffect } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Grid,
    TextField,
    Autocomplete,
    Button,
    Alert,
    Chip,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    alpha,
    useTheme,
    Skeleton,
    Divider,
    MenuItem,
    Select,
    FormControl,
    InputLabel,
} from '@mui/material';
import {
    PictureAsPdf,
    TableChart,
    Search,
} from '@mui/icons-material';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer,
} from 'recharts';
import api from '../../services/api';

export default function VMDetailReport() {
    const theme = useTheme();
    const [loading, setLoading] = useState(false);
    const [vmList, setVmList] = useState<any[]>([]);
    const [selectedVm, setSelectedVm] = useState<any>(null);
    const [days, setDays] = useState(7);
    const [reportData, setReportData] = useState<any>(null);
    const [error, setError] = useState('');

    // Fetch VM list
    useEffect(() => {
        const fetchVmList = async () => {
            try {
                const response = await api.get('/vms?page=1&page_size=500');
                // /vms API returns {items, total, page, page_size, pages}
                if (response.data && response.data.items) {
                    setVmList(response.data.items);
                }
            } catch (err) {
                console.error('Failed to fetch VM list:', err);
            }
        };
        fetchVmList();
    }, []);

    // Fetch report data when VM is selected
    const fetchReport = async () => {
        if (!selectedVm) return;

        try {
            setLoading(true);
            setError('');
            const response = await api.get(`/vmreport/vm-detail/${selectedVm.vm_uuid}?days=${days}`);
            if (response.data.success) {
                setReportData(response.data.data);
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'เกิดข้อผิดพลาดในการโหลดข้อมูล');
        } finally {
            setLoading(false);
        }
    };

    return (
        <Box className="space-y-4">
            {/* Search Bar */}
            <Card
                elevation={0}
                sx={{
                    bgcolor: alpha(theme.palette.background.paper, 0.6),
                    border: `1px solid ${theme.palette.divider}`,
                    borderRadius: 3,
                }}
            >
                <CardContent className="p-4">
                    <Grid container spacing={2} alignItems="center">
                        <Grid item xs={12} md={6}>
                            <Autocomplete
                                options={vmList}
                                getOptionLabel={(option) => option.name || ''}
                                value={selectedVm}
                                onChange={(_e, newValue) => setSelectedVm(newValue)}
                                renderInput={(params) => (
                                    <TextField
                                        {...params}
                                        label="เลือก VM"
                                        placeholder="ค้นหาชื่อ VM..."
                                        variant="outlined"
                                        fullWidth
                                    />
                                )}
                            />
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                            <FormControl fullWidth>
                                <InputLabel>ช่วงเวลา</InputLabel>
                                <Select
                                    value={days}
                                    label="ช่วงเวลา"
                                    onChange={(e) => setDays(Number(e.target.value))}
                                >
                                    <MenuItem value={1}>24 ชั่วโมง</MenuItem>
                                    <MenuItem value={7}>7 วัน</MenuItem>
                                    <MenuItem value={30}>30 วัน</MenuItem>
                                    <MenuItem value={90}>90 วัน</MenuItem>
                                </Select>
                            </FormControl>
                        </Grid>
                        <Grid item xs={12} sm={6} md={3}>
                            <Button
                                variant="contained"
                                fullWidth
                                startIcon={<Search />}
                                onClick={fetchReport}
                                disabled={!selectedVm || loading}
                                sx={{ height: 56, borderRadius: 2, textTransform: 'none', fontWeight: 600 }}
                            >
                                สร้างรายงาน
                            </Button>
                        </Grid>
                    </Grid>
                </CardContent>
            </Card>

            {/* Error */}
            {error && (
                <Alert severity="error" onClose={() => setError('')}>
                    {error}
                </Alert>
            )}

            {/* Loading */}
            {loading && (
                <Box className="space-y-4">
                    <Skeleton variant="rectangular" height={200} sx={{ borderRadius: 2 }} />
                    <Skeleton variant="rectangular" height={300} sx={{ borderRadius: 2 }} />
                </Box>
            )}

            {/* Report Data */}
            {!loading && reportData && (
                <Box className="space-y-4">
                    {/* Basic Info */}
                    <Card
                        elevation={0}
                        sx={{
                            bgcolor: alpha(theme.palette.primary.main, 0.05),
                            border: `1px solid ${alpha(theme.palette.primary.main, 0.2)}`,
                            borderRadius: 3,
                        }}
                    >
                        <CardContent className="p-4">
                            <Typography variant="h6" fontWeight={700} gutterBottom>
                                ข้อมูลพื้นฐาน
                            </Typography>
                            <Grid container spacing={2}>
                                <Grid item xs={12} sm={6} md={3}>
                                    <Typography variant="caption" color="text.secondary">ชื่อ VM</Typography>
                                    <Typography variant="body1" fontWeight={600}>{reportData.basic_info.vm_name}</Typography>
                                </Grid>
                                <Grid item xs={12} sm={6} md={3}>
                                    <Typography variant="caption" color="text.secondary">Host</Typography>
                                    <Typography variant="body1" fontWeight={600}>{reportData.basic_info.host_name || 'N/A'}</Typography>
                                </Grid>
                                <Grid item xs={12} sm={6} md={2}>
                                    <Typography variant="caption" color="text.secondary">vCPU</Typography>
                                    <Typography variant="body1" fontWeight={600}>{reportData.basic_info.vcpu} cores</Typography>
                                </Grid>
                                <Grid item xs={12} sm={6} md={2}>
                                    <Typography variant="caption" color="text.secondary">vRAM</Typography>
                                    <Typography variant="body1" fontWeight={600}>{(reportData.basic_info.vram_mb / 1024).toFixed(1)} GB</Typography>
                                </Grid>
                                <Grid item xs={12} sm={6} md={2}>
                                    <Typography variant="caption" color="text.secondary">Disk</Typography>
                                    <Typography variant="body1" fontWeight={600}>{reportData.basic_info.disk_total_gb} GB</Typography>
                                </Grid>
                            </Grid>
                        </CardContent>
                    </Card>

                    {/* Snapshot */}
                    <Card elevation={0} sx={{ bgcolor: alpha(theme.palette.background.paper, 0.6), border: `1px solid ${theme.palette.divider}`, borderRadius: 3 }}>
                        <CardContent className="p-4">
                            <Typography variant="h6" fontWeight={700} gutterBottom>Snapshot ปัจจุบัน</Typography>
                            <Grid container spacing={2}>
                                <Grid item xs={6} sm={3}>
                                    <Box className="text-center">
                                        <Typography variant="h4" fontWeight={800} color="primary">{reportData.snapshot.cpu_percent}%</Typography>
                                        <Typography variant="caption" color="text.secondary">CPU</Typography>
                                    </Box>
                                </Grid>
                                <Grid item xs={6} sm={3}>
                                    <Box className="text-center">
                                        <Typography variant="h4" fontWeight={800} color="secondary">{reportData.snapshot.memory_percent}%</Typography>
                                        <Typography variant="caption" color="text.secondary">RAM</Typography>
                                    </Box>
                                </Grid>
                                <Grid item xs={6} sm={3}>
                                    <Box className="text-center">
                                        <Typography variant="h4" fontWeight={800} color="warning.main">{reportData.snapshot.disk_percent}%</Typography>
                                        <Typography variant="caption" color="text.secondary">Disk</Typography>
                                    </Box>
                                </Grid>
                                <Grid item xs={6} sm={3}>
                                    <Box className="text-center">
                                        <Typography variant="h4" fontWeight={800} color="info.main">{reportData.snapshot.network_in_mbps.toFixed(2)}</Typography>
                                        <Typography variant="caption" color="text.secondary">Network IN (MB/s)</Typography>
                                    </Box>
                                </Grid>
                            </Grid>
                        </CardContent>
                    </Card>

                    {/* Historical Chart */}
                    <Card elevation={0} sx={{ bgcolor: alpha(theme.palette.background.paper, 0.6), border: `1px solid ${theme.palette.divider}`, borderRadius: 3 }}>
                        <CardContent className="p-4">
                            <Typography variant="h6" fontWeight={700} gutterBottom>กราฟย้อนหลัง {days} วัน</Typography>
                            <ResponsiveContainer width="100%" height={300}>
                                <LineChart data={reportData.historical_data}>
                                    <CartesianGrid strokeDasharray="3 3" stroke={theme.palette.divider} />
                                    <XAxis dataKey="date" stroke={theme.palette.text.secondary} style={{ fontSize: '12px' }} />
                                    <YAxis stroke={theme.palette.text.secondary} style={{ fontSize: '12px' }} />
                                    <Tooltip contentStyle={{ backgroundColor: theme.palette.background.paper, border: `1px solid ${theme.palette.divider}` }} />
                                    <Legend />
                                    <Line type="monotone" dataKey="cpu_avg" stroke={theme.palette.primary.main} name="CPU" strokeWidth={2} />
                                    <Line type="monotone" dataKey="memory_avg" stroke={theme.palette.secondary.main} name="RAM" strokeWidth={2} />
                                    <Line type="monotone" dataKey="disk_avg" stroke={theme.palette.warning.main} name="Disk" strokeWidth={2} />
                                </LineChart>
                            </ResponsiveContainer>
                        </CardContent>
                    </Card>

                    {/* Statistics Table */}
                    <Card elevation={0} sx={{ bgcolor: alpha(theme.palette.background.paper, 0.6), border: `1px solid ${theme.palette.divider}`, borderRadius: 3 }}>
                        <CardContent className="p-4">
                            <Box className="flex justify-between items-center mb-4">
                                <Typography variant="h6" fontWeight={700}>ตารางสถิติ</Typography>
                                <Box className="flex gap-2">
                                    <Button size="small" startIcon={<PictureAsPdf />} variant="outlined">PDF</Button>
                                    <Button size="small" startIcon={<TableChart />} variant="outlined">Excel</Button>
                                </Box>
                            </Box>
                            <TableContainer>
                                <Table>
                                    <TableHead>
                                        <TableRow>
                                            <TableCell>รายการ</TableCell>
                                            <TableCell align="right">ค่าเฉลี่ย</TableCell>
                                            <TableCell align="right">ค่าสูงสุด</TableCell>
                                            <TableCell align="right">ค่าต่ำสุด</TableCell>
                                            <TableCell align="right">P95</TableCell>
                                        </TableRow>
                                    </TableHead>
                                    <TableBody>
                                        {reportData.statistics.map((row: any, index: number) => (
                                            <TableRow key={index}>
                                                <TableCell component="th" scope="row" sx={{ fontWeight: 600 }}>{row.metric}</TableCell>
                                                <TableCell align="right">{row.avg}%</TableCell>
                                                <TableCell align="right">{row.max}%</TableCell>
                                                <TableCell align="right">{row.min}%</TableCell>
                                                <TableCell align="right">{row.p95 ? `${row.p95}%` : 'N/A'}</TableCell>
                                            </TableRow>
                                        ))}
                                    </TableBody>
                                </Table>
                            </TableContainer>
                        </CardContent>
                    </Card>

                    {/* Health Analysis */}
                    {reportData.health_analysis && (
                        <Card elevation={0} sx={{ bgcolor: alpha(theme.palette.background.paper, 0.6), border: `1px solid ${theme.palette.divider}`, borderRadius: 3 }}>
                            <CardContent className="p-4">
                                <Typography variant="h6" fontWeight={700} gutterBottom>วิเคราะห์แนวโน้ม</Typography>
                                <Box className="space-y-2">
                                    <Box className="flex items-center gap-2">
                                        <Typography variant="body2" fontWeight={600}>คะแนนสุขภาพ:</Typography>
                                        <Chip
                                            label={`${reportData.health_analysis.score} / 100`}
                                            color={reportData.health_analysis.score >= 80 ? 'success' : reportData.health_analysis.score >= 50 ? 'warning' : 'error'}
                                            sx={{ fontWeight: 700 }}
                                        />
                                        <Chip label={reportData.health_analysis.risk_level} size="small" />
                                    </Box>
                                    <Divider />
                                    {reportData.health_analysis.recommendations.length > 0 && (
                                        <Box>
                                            <Typography variant="body2" fontWeight={600} gutterBottom>ข้อเสนอแนะ:</Typography>
                                            <Box component="ul" className="ml-4 space-y-1">
                                                {reportData.health_analysis.recommendations.map((rec: string, i: number) => (
                                                    <Typography key={i} component="li" variant="body2" color="text.secondary">
                                                        {rec}
                                                    </Typography>
                                                ))}
                                            </Box>
                                        </Box>
                                    )}
                                </Box>
                            </CardContent>
                        </Card>
                    )}
                </Box>
            )}

            {/* Empty State */}
            {!loading && !reportData && !error && (
                <Card elevation={0}sx={{ bgcolor: alpha(theme.palette.background.paper, 0.6), border: `1px solid ${theme.palette.divider}`, borderRadius: 3 }}>
                    <CardContent className="p-8 text-center">
                        <Search sx={{ fontSize: 80, color: 'text.disabled', mb: 2 }} />
                        <Typography variant="h6" color="text.secondary" gutterBottom>
                            เลือก VM เพื่อดูรายงาน
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                            กรุณาเลือก VM และช่วงเวลาที่ต้องการ จากนั้นกดปุ่ม "สร้างรายงาน"
                        </Typography>
                    </CardContent>
                </Card>
            )}
        </Box>
    );
}
