/**
 * Efficiency Report Component
 * รายงานประสิทธิภาพ - VM ที่ Over-Provision และ Idle
 */

import { useState, useEffect } from 'react';
import {
    Box,
    Card,
    CardContent,
    Typography,
    Button,
    Alert,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Chip,
    alpha,
    useTheme,
    CircularProgress,
    Grid,
} from '@mui/material';
import { Download } from '@mui/icons-material';
import api from '../../services/api';

export default function EfficiencyReport() {
    const theme = useTheme();
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState<any[]>([]);
    const [summary, setSummary] = useState({ over_provisioned_count: 0, idle_count: 0 });
    const [error, setError] = useState('');

    const fetchData = async () => {
        try {
            setLoading(true);
            setError('');
            const response = await api.get('/vmreport/efficiency');
            if (response.data.success) {
                setData(response.data.data);
                setSummary(response.data.summary);
            }
        } catch (err: any) {
            setError(err.response?.data?.detail || 'เกิดข้อผิดพลาด');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchData();
    }, []);

    return (
        <Box className="space-y-4">
            {/* Summary Cards */}
            <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                    <Card elevation={0} sx={{ bgcolor: alpha(theme.palette.warning.main, 0.1), border: `1px solid ${alpha(theme.palette.warning.main, 0.3)}`, borderRadius: 3 }}>
                        <CardContent>
                            <Typography variant="body2" color="text.secondary" gutterBottom>VM ที่จัดสรรเกิน</Typography>
                            <Typography variant="h3" fontWeight={800} color="warning.main">{summary.over_provisioned_count}</Typography>
                            <Typography variant="caption" color="text.secondary">สามารถลดทรัพยากรได้</Typography>
                        </CardContent>
                    </Card>
                </Grid>
                <Grid item xs={12} sm={6}>
                    <Card elevation={0} sx={{ bgcolor: alpha(theme.palette.info.main, 0.1), border: `1px solid ${alpha(theme.palette.info.main, 0.3)}`, borderRadius: 3 }}>
                        <CardContent>
                            <Typography variant="body2" color="text.secondary" gutterBottom>VM ที่ใช้งานน้อย</Typography>
                            <Typography variant="h3" fontWeight={800} color="info.main">{summary.idle_count}</Typography>
                            <Typography variant="caption" color="text.secondary">ควรพิจารณาปิด</Typography>
                        </CardContent>
                    </Card>
                </Grid>
            </Grid>

            {error && <Alert severity="error">{error}</Alert>}

            {loading ? (
                <Box className="flex justify-center p-8">
                    <CircularProgress />
                </Box>
            ) : (
                <Card elevation={0} sx={{ bgcolor: alpha(theme.palette.background.paper, 0.6), border: `1px solid ${theme.palette.divider}`, borderRadius: 3 }}>
                    <CardContent className="p-4">
                        <Box className="flex justify-between items-center mb-4">
                            <Typography variant="h6" fontWeight={700}>
                                รายการ VM ที่ควรปรับปรุง ({data.length} รายการ)
                            </Typography>
                            <Button variant="outlined" startIcon={<Download />}>
                                ส่งออก Excel
                            </Button>
                        </Box>

                        <TableContainer>
                            <Table>
                                <TableHead>
                                    <TableRow>
                                        <TableCell>ชื่อ VM</TableCell>
                                        <TableCell align="center">vCPU</TableCell>
                                        <TableCell align="center">vRAM (MB)</TableCell>
                                        <TableCell align="center">CPU %</TableCell>
                                        <TableCell align="center">RAM %</TableCell>
                                        <TableCell align="center">Disk %</TableCell>
                                        <TableCell>สถานะ</TableCell>
                                        <TableCell>คะแนนสุขภาพ</TableCell>
                                        <TableCell>ข้อเสนอแนะ</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {data.map((row, index) => (
                                        <TableRow key={index}>
                                            <TableCell sx={{ fontWeight: 600 }}>{row.vm_name}</TableCell>
                                            <TableCell align="center">{row.vcpu}</TableCell>
                                            <TableCell align="center">{row.vram_mb}</TableCell>
                                            <TableCell align="center">{row.cpu_avg_percent}%</TableCell>
                                            <TableCell align="center">{row.memory_avg_percent}%</TableCell>
                                            <TableCell align="center">{row.disk_avg_percent}%</TableCell>
                                            <TableCell>
                                                <Box className="flex gap-1">
                                                    {row.is_over_provisioned && <Chip label="Over-Provision" size="small" color="warning" />}
                                                    {row.is_idle && <Chip label="Idle" size="small" color="info" />}
                                                </Box>
                                            </TableCell>
                                            <TableCell>
                                                <Chip
                                                    label={row.health_score}
                                                    size="small"
                                                    color={row.health_score >= 80 ? 'success' : row.health_score >= 50 ? 'warning' : 'error'}
                                                    sx={{ fontWeight: 700 }}
                                                />
                                            </TableCell>
                                            <TableCell sx={{ maxWidth: 200 }}>
                                                <Typography variant="caption" color="text.secondary">
                                                    {row.recommendations.slice(0, 2).join(', ')}
                                                </Typography>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        </TableContainer>
                    </CardContent>
                </Card>
            )}
        </Box>
    );
}
