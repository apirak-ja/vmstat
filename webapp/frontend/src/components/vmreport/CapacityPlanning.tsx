/**
 * Capacity Planning Component
 * รายงานการวางแผนความจุ
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
    FormControl,
    InputLabel,
    Select,
    MenuItem,
    Checkbox,
    FormControlLabel,
} from '@mui/material';
import { Download, Warning } from '@mui/icons-material';
import api from '../../services/api';

export default function CapacityPlanning() {
    const theme = useTheme();
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState<any[]>([]);
    const [error, setError] = useState('');
    const [resourceType, setResourceType] = useState<string>('');
    const [criticalOnly, setCriticalOnly] = useState(false);

    const fetchData = async () => {
        try {
            setLoading(true);
            setError('');
            const params = new URLSearchParams();
            if (resourceType) params.append('resource_type', resourceType);
            if (criticalOnly) params.append('critical_only', 'true');

            const response = await api.get(`/vmreport/capacity-planning?${params.toString()}`);
            if (response.data.success) {
                setData(response.data.data);
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
            {/* Filters */}
            <Card elevation={0} sx={{ bgcolor: alpha(theme.palette.background.paper, 0.6), border: `1px solid ${theme.palette.divider}`, borderRadius: 3 }}>
                <CardContent className="p-4">
                    <Box className="flex flex-wrap gap-4 items-center">
                        <FormControl sx={{ minWidth: 200 }}>
                            <InputLabel>ประเภททรัพยากร</InputLabel>
                            <Select
                                value={resourceType}
                                label="ประเภททรัพยากร"
                                onChange={(e) => setResourceType(e.target.value)}
                            >
                                <MenuItem value="">ทั้งหมด</MenuItem>
                                <MenuItem value="disk">พื้นที่ดิสก์</MenuItem>
                                <MenuItem value="memory">หน่วยความจำ</MenuItem>
                                <MenuItem value="cpu">CPU</MenuItem>
                            </Select>
                        </FormControl>
                        <FormControlLabel
                            control={<Checkbox checked={criticalOnly} onChange={(e) => setCriticalOnly(e.target.checked)} />}
                            label="แสดงเฉพาะ VM วิกฤติ (< 30 วัน)"
                        />
                        <Button variant="contained" onClick={fetchData} disabled={loading}>
                            ค้นหา
                        </Button>
                        <Button variant="outlined" startIcon={<Download />} className="ml-auto">
                            ส่งออก Excel
                        </Button>
                    </Box>
                </CardContent>
            </Card>

            {error && <Alert severity="error">{error}</Alert>}

            {loading ? (
                <Box className="flex justify-center p-8">
                    <CircularProgress />
                </Box>
            ) : (
                <Card elevation={0} sx={{ bgcolor: alpha(theme.palette.background.paper, 0.6), border: `1px solid ${theme.palette.divider}`, borderRadius: 3 }}>
                    <CardContent className="p-4">
                        <Typography variant="h6" fontWeight={700} gutterBottom>
                            ผลการพยากรณ์ ({data.length} รายการ)
                        </Typography>
                        <TableContainer>
                            <Table>
                                <TableHead>
                                    <TableRow>
                                        <TableCell>ชื่อ VM</TableCell>
                                        <TableCell>ทรัพยากร</TableCell>
                                        <TableCell align="right">ใช้งานปัจจุบัน</TableCell>
                                        <TableCell align="right">อัตราเติบโต/วัน</TableCell>
                                        <TableCell align="right">เต็มใน (วัน)</TableCell>
                                        <TableCell>วันที่คาดว่าจะเต็ม</TableCell>
                                        <TableCell>ความเชื่อมั่น</TableCell>
                                    </TableRow>
                                </TableHead>
                                <TableBody>
                                    {data.map((row, index) => (
                                        <TableRow key={index}>
                                            <TableCell sx={{ fontWeight: 600 }}>{row.vm_name}</TableCell>
                                            <TableCell>
                                                <Chip label={row.resource_type.toUpperCase()} size="small" />
                                            </TableCell>
                                            <TableCell align="right">{row.current_usage_percent}%</TableCell>
                                            <TableCell align="right">+{row.growth_rate_per_day}%</TableCell>
                                            <TableCell align="right">
                                                <Chip
                                                    label={row.days_until_full || 'N/A'}
                                                    size="small"
                                                    color={row.days_until_full < 30 ? 'error' : row.days_until_full < 60 ? 'warning' : 'success'}
                                                    icon={row.days_until_full < 30 ? <Warning /> : undefined}
                                                    sx={{ fontWeight: 700 }}
                                                />
                                            </TableCell>
                                            <TableCell>{row.estimated_full_date || 'N/A'}</TableCell>
                                            <TableCell>
                                                <Chip label={row.confidence_level} size="small" variant="outlined" />
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
