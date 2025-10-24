import { useCallback, useMemo, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Container,
  Divider,
  Grid,
  Paper,
  Stack,
  TextField,
  Typography,
} from '@mui/material';
import { routeRequest } from './api';
import type { FormState, RouterResponse } from './types';

const initialFormState: FormState = {
  sessionId: 'demo-session',
  scripture: '约翰福音3:16',
  userQuestion: '这段经文如何应用？',
  userProfile: {
    age_group: '25-35',
    profession: '教师',
    concerns: ['家庭', '教会事奉'],
  },
  spiritualState: '疲惫但渴望神',
  sessionStage: '初访',
  historySummary: '',
};

function App() {
  const [form, setForm] = useState<FormState>(initialFormState);
  const [concernsText, setConcernsText] = useState(form.userProfile.concerns.join(', '));
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [response, setResponse] = useState<RouterResponse | null>(null);

  const handleChange = useCallback(<K extends keyof FormState>(key: K, value: FormState[K]) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  }, []);

  const handleProfileChange = useCallback(<K extends keyof FormState['userProfile']>(
    key: K,
    value: FormState['userProfile'][K],
  ) => {
    setForm((prev) => ({
      ...prev,
      userProfile: {
        ...prev.userProfile,
        [key]: value,
      },
    }));
  }, []);

  const handleSubmit = useCallback(async () => {
    setLoading(true);
    setError(null);
    setResponse(null);

    const cleanConcerns = concernsText
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);

    const payload = {
      scripture: form.scripture,
      user_question: form.userQuestion,
      user_profile: {
        age_group: form.userProfile.age_group,
        profession: form.userProfile.profession,
        concerns: cleanConcerns,
      },
      spiritual_state: form.spiritualState,
      session_stage: form.sessionStage,
      history_summary: form.historySummary || undefined,
    };

    try {
      const result = await routeRequest({
        session_id: form.sessionId,
        payload,
      });
      setResponse(result);
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : '调用路由服务失败');
    } finally {
      setLoading(false);
    }
  }, [concernsText, form]);

  const selectedRoles = useMemo(() => response?.decision.selected_roles ?? [], [response]);

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        DevoLight 元调度器 MVP
      </Typography>
      <Typography variant="body1" color="text.secondary" gutterBottom>
        输入会话信息，调用后端路由服务，查看元调度者决策与角色输出。
      </Typography>

      <Grid container spacing={3} alignItems="flex-start">
        <Grid item xs={12} md={5}>
          <Paper elevation={3} sx={{ p: 3 }}>
            <Stack spacing={2}>
              <TextField
                label="Session ID"
                fullWidth
                value={form.sessionId}
                onChange={(event) => handleChange('sessionId', event.target.value)}
              />
              <TextField
                label="经文章节"
                fullWidth
                value={form.scripture}
                onChange={(event) => handleChange('scripture', event.target.value)}
              />
              <TextField
                label="用户问题"
                fullWidth
                multiline
                minRows={2}
                value={form.userQuestion}
                onChange={(event) => handleChange('userQuestion', event.target.value)}
              />
              <Stack direction="row" spacing={2}>
                <TextField
                  label="年龄段"
                  fullWidth
                  value={form.userProfile.age_group}
                  onChange={(event) => handleProfileChange('age_group', event.target.value)}
                />
                <TextField
                  label="职业"
                  fullWidth
                  value={form.userProfile.profession}
                  onChange={(event) => handleProfileChange('profession', event.target.value)}
                />
              </Stack>
              <TextField
                label="关注点（逗号分隔）"
                fullWidth
                value={concernsText}
                onChange={(event) => setConcernsText(event.target.value)}
              />
              <TextField
                label="灵性状态"
                fullWidth
                value={form.spiritualState}
                onChange={(event) => handleChange('spiritualState', event.target.value)}
              />
              <TextField
                label="会话阶段"
                fullWidth
                value={form.sessionStage}
                onChange={(event) => handleChange('sessionStage', event.target.value)}
              />
              <TextField
                label="历史摘要（可选）"
                fullWidth
                multiline
                minRows={2}
                value={form.historySummary}
                onChange={(event) => handleChange('historySummary', event.target.value)}
              />
              <Box display="flex" justifyContent="flex-end">
                <Button
                  variant="contained"
                  size="large"
                  onClick={handleSubmit}
                  disabled={loading}
                >
                  {loading ? <CircularProgress size={24} /> : '提交请求'}
                </Button>
              </Box>
              {error && <Alert severity="error">{error}</Alert>}
            </Stack>
          </Paper>
        </Grid>

        <Grid item xs={12} md={7}>
          <Stack spacing={2}>
            {response ? (
              <>
                <Paper elevation={3} sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    元调度者决策
                  </Typography>
                  <Typography variant="subtitle1">模式：{response.decision.mode}</Typography>
                  <Typography variant="body1" sx={{ mt: 1 }}>
                    {response.decision.overall_rationale}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    兜底策略：{response.decision.fallback_plan}
                  </Typography>
                  {response.decision.warnings.length > 0 && (
                    <Alert severity="warning" sx={{ mt: 2 }}>
                      {response.decision.warnings.map((warning) => (
                        <div key={warning}>{warning}</div>
                      ))}
                    </Alert>
                  )}
                </Paper>

                <Paper elevation={3} sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    角色编排
                  </Typography>
                  {selectedRoles.length > 0 ? (
                    <Stack spacing={1}>
                      <Stack direction="row" flexWrap="wrap" gap={1}>
                        {selectedRoles.map((role) => (
                          <Chip
                            key={role.name}
                            label={`${role.name} · ${role.score.toFixed(2)}`}
                            color="primary"
                            variant="outlined"
                          />
                        ))}
                      </Stack>
                      <Divider sx={{ my: 1 }} />
                      {selectedRoles.map((role) => (
                        <Box key={role.name}>
                          <Typography variant="subtitle1">{role.name}</Typography>
                          <Typography variant="body2" color="text.secondary">
                            {role.reason}
                          </Typography>
                          <Typography variant="body2" sx={{ mt: 0.5 }}>
                            交接提示：{role.handoff_note}
                          </Typography>
                        </Box>
                      ))}
                    </Stack>
                  ) : (
                    <Typography color="text.secondary">暂无角色调度。</Typography>
                  )}
                </Paper>

                <Paper elevation={3} sx={{ p: 3 }}>
                  <Typography variant="h6" gutterBottom>
                    角色输出
                  </Typography>
                  <Stack spacing={2}>
                    {response.role_outputs.map((output) => (
                      <Box key={output.role_name}>
                        <Typography variant="subtitle1" gutterBottom>
                          {output.role_name}
                        </Typography>
                        <Paper variant="outlined" sx={{ p: 2, whiteSpace: 'pre-wrap' }}>
                          {output.content}
                        </Paper>
                      </Box>
                    ))}
                  </Stack>
                </Paper>

                {response.warnings.length > 0 && (
                  <Paper elevation={0} sx={{ p: 2 }}>
                    <Alert severity="info">
                      {response.warnings.map((warning) => (
                        <div key={warning}>{warning}</div>
                      ))}
                    </Alert>
                  </Paper>
                )}
              </>
            ) : (
              <Paper elevation={1} sx={{ p: 3 }}>
                <Typography color="text.secondary">
                  填写表单后点击“提交请求”即可查看决策结果。
                </Typography>
              </Paper>
            )}
          </Stack>
        </Grid>
      </Grid>
    </Container>
  );
}

export default App;
