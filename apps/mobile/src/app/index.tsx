import { useState } from 'react';
import { ActivityIndicator, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Switch, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { DailyAction, request } from '../api';

const scale = [1, 2, 3, 4, 5];

function Button({ title, onPress, disabled = false, secondary = false }: {
  title: string; onPress: () => void; disabled?: boolean; secondary?: boolean;
}) {
  return <Pressable accessibilityRole="button" accessibilityState={{ disabled }} disabled={disabled}
    onPress={onPress} style={[styles.button, secondary && styles.secondary, disabled && styles.disabled]}>
    <Text style={[styles.buttonText, secondary && styles.secondaryText]}>{title}</Text>
  </Pressable>;
}

function Rating({ label, value, onChange }: { label: string; value: number | null; onChange: (value: number | null) => void }) {
  return <View style={styles.field}><Text style={styles.label}>{label}</Text>
    <View style={styles.row}>{scale.map(number => <Pressable key={number} accessibilityRole="radio"
      accessibilityLabel={`${label}: ${number} of 5`} accessibilityState={{ checked: value === number }}
      onPress={() => onChange(value === number ? null : number)} style={[styles.rating, value === number && styles.selected]}>
      <Text style={[styles.body, value === number && styles.buttonText]}>{number}</Text>
    </Pressable>)}</View><Text style={styles.muted}>Optional · tap again to clear</Text>
  </View>;
}

export default function Home() {
  const [base, setBase] = useState('http://127.0.0.1:8000');
  const [token, setToken] = useState('');
  const [connected, setConnected] = useState(false);
  const [minutes, setMinutes] = useState('10');
  const [sleep, setSleep] = useState('');
  const [energy, setEnergy] = useState<number | null>(null);
  const [stress, setStress] = useState<number | null>(null);
  const [movement, setMovement] = useState(true);
  const [history, setHistory] = useState<DailyAction[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  const today = new Intl.DateTimeFormat('en-CA', { timeZone: timezone, year: 'numeric', month: '2-digit', day: '2-digit' })
    .formatToParts(new Date());
  const datePart = (type: string) => today.find(part => part.type === type)?.value;
  const localDate = `${datePart('year')}-${datePart('month')}-${datePart('day')}`;
  const current = history.find(row => row.local_date === localDate);

  async function perform(work: () => Promise<void>) {
    setBusy(true); setError('');
    try { await work(); } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to connect. Please try again.');
    } finally { setBusy(false); }
  }

  async function refresh() {
    const rows = await request<DailyAction[]>(base, token, '/v1/history');
    setHistory(rows); setConnected(true);
  }

  function submit() {
    void perform(async () => {
      const available = Number(minutes);
      const hours = sleep.trim() ? Number(sleep) : null;
      if (!Number.isInteger(available) || available < 1 || available > 120 ||
          (hours !== null && (!Number.isFinite(hours) || hours < 0 || hours > 24))) {
        throw new Error('Enter 1–120 available minutes and, optionally, 0–24 hours of sleep.');
      }
      await request<DailyAction>(base, token, '/v1/check-ins', {
        timezone, available_minutes: available, energy, stress, sleep_hours: hours, allow_movement: movement,
      }, 'POST');
      await refresh();
    });
  }

  function feedback(status: 'completed' | 'skipped', helpful: boolean | null) {
    if (!current) return;
    void perform(async () => {
      await request(base, token, `/v1/recommendations/${current.id}/feedback`, { status, helpful }, 'PUT');
      await refresh();
    });
  }

  return <SafeAreaView style={styles.safe}><KeyboardAvoidingView style={styles.safe}
    behavior={Platform.OS === 'ios' ? 'padding' : undefined}><ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
    <Text style={styles.brand}>centered</Text><Text style={styles.eyebrow}>A LITTLE SPACE FOR YOURSELF</Text>
    <Text style={styles.heading}>One thing.{ '\n' }For today.</Text>
    <Text style={styles.intro}>Start with how you feel. No wearable needed.</Text>
    <View style={styles.notice}><Text style={styles.label}>Development preview</Text>
      <Text style={styles.body}>Sample actions await evidence review. Use synthetic inputs only. Wearable connections and personal sign-in are coming later.</Text></View>
    {!connected ? <View style={styles.card}>
      <Text style={styles.title}>Connect your local API</Text>
      <Text style={styles.label}>API address</Text><TextInput accessibilityLabel="API address" style={styles.input} value={base} onChangeText={setBase} autoCapitalize="none" autoCorrect={false} keyboardType="url" />
      <Text style={styles.label}>Development token</Text><TextInput accessibilityLabel="Development token" style={styles.input} value={token} onChangeText={setToken} secureTextEntry autoCapitalize="none" autoCorrect={false} />
      <Text style={styles.muted}>Token stays in memory. Use only your own trusted development API.</Text>
      <Button title="Connect" disabled={busy || token.length < 24} onPress={() => { void perform(refresh); }} />
    </View> : <>
      {!current ? <View style={styles.card}>
        <Text style={styles.title}>How is today looking?</Text><Text style={styles.muted}>{localDate} · {timezone}</Text>
        <Rating label="Energy · 1 low, 5 high" value={energy} onChange={setEnergy} />
        <Rating label="Stress · 1 low, 5 high" value={stress} onChange={setStress} />
        <Text style={styles.label}>Minutes you can spare</Text><TextInput accessibilityLabel="Available minutes" style={styles.input} value={minutes} onChangeText={setMinutes} keyboardType="number-pad" />
        <Text style={styles.label}>Hours slept · optional</Text><TextInput accessibilityLabel="Hours slept" style={styles.input} value={sleep} onChangeText={setSleep} keyboardType="decimal-pad" placeholder="Unknown" />
        <View style={styles.switchRow}><Text style={styles.body}>Include gentle movement</Text><Switch accessibilityLabel="Allow movement" value={movement} onValueChange={setMovement} /></View>
        <Button title="Find today's action" onPress={submit} disabled={busy} />
      </View> : <View style={styles.card}>
        <Text style={styles.eyebrow}>TODAY’S ACTION</Text><Text style={styles.title}>{current.decision.action?.title ?? 'No suitable action yet'}</Text>
        {current.decision.action && <Text style={styles.duration}>{current.decision.action.minutes} minutes · manual context</Text>}
        <Text style={styles.label}>Why this fits</Text><Text style={styles.body}>{current.decision.reason}</Text>
        <Text style={styles.muted}>Evidence review pending · no impact or confidence claim</Text>
        {current.feedback ? <Text accessibilityLiveRegion="polite" style={styles.duration}>{current.feedback.status === 'completed' ? 'Recorded. Thank you for checking in.' : 'Skipped. Tomorrow is another day.'}</Text> : current.decision.action ? <>
          <Button title="Completed · felt helpful" disabled={busy} onPress={() => feedback('completed', true)} />
          <Button title="Completed · wasn't helpful" secondary disabled={busy} onPress={() => feedback('completed', false)} />
          <Button title="Skip today" secondary disabled={busy} onPress={() => feedback('skipped', null)} />
        </> : null}
      </View>}
      <Button title="Refresh history" secondary disabled={busy} onPress={() => { void perform(refresh); }} />
      <Text style={styles.title}>Your recent days</Text>
      {history.length === 0 && <Text style={styles.muted}>Your first check-in will appear here.</Text>}
      {history.map(row => <View style={styles.history} key={row.id}><Text style={styles.label}>{row.local_date}</Text>
        <Text style={styles.body}>{row.decision.action?.title ?? 'No suitable action'}</Text><Text style={styles.muted}>{row.feedback?.status ?? 'Awaiting feedback'}</Text></View>)}
      <Button title="Disconnect local API" secondary disabled={busy} onPress={() => { setConnected(false); setToken(''); setHistory([]); setError(''); }} />
    </>}
    {busy && <ActivityIndicator color="#345448" accessibilityLabel="Loading" />}
    {!!error && <Text accessibilityRole="alert" style={styles.error}>{error}</Text>}
    <Text style={styles.footer}>Progress, without pressure.</Text>
  </ScrollView></KeyboardAvoidingView></SafeAreaView>;
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: '#F5F3EC' },
  content: { padding: 24, gap: 18, maxWidth: 620, width: '100%', alignSelf: 'center' },
  brand: { fontSize: 26, letterSpacing: -1, fontWeight: '600', color: '#243F34' },
  eyebrow: { fontSize: 11, letterSpacing: 2, color: '#526A5B', fontWeight: '700' },
  heading: { fontSize: 52, lineHeight: 56, letterSpacing: -2, color: '#243F34', fontWeight: '500' },
  intro: { fontSize: 17, lineHeight: 26, color: '#536456' },
  notice: { backgroundColor: '#EAE5D7', padding: 16, borderRadius: 12, gap: 8 },
  card: { backgroundColor: '#FFFFFF', padding: 22, borderRadius: 20, gap: 16 },
  title: { fontSize: 25, lineHeight: 32, color: '#243F34', fontWeight: '500' },
  label: { fontSize: 14, color: '#34483D', fontWeight: '600' },
  body: { fontSize: 15, lineHeight: 23, color: '#34483D' },
  muted: { fontSize: 12, lineHeight: 19, color: '#626B61' },
  duration: { fontSize: 14, color: '#345448', fontWeight: '600' },
  input: { borderColor: '#CCD3C9', borderWidth: 1, borderRadius: 10, padding: 13, minHeight: 48, fontSize: 16, color: '#243F34' },
  field: { gap: 10 }, row: { flexDirection: 'row', gap: 8, flexWrap: 'wrap' },
  rating: { minWidth: 44, minHeight: 44, alignItems: 'center', justifyContent: 'center', borderRadius: 22, backgroundColor: '#EBEFE8' },
  selected: { backgroundColor: '#345448' },
  switchRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: 8, flexWrap: 'wrap' },
  button: { backgroundColor: '#345448', padding: 15, minHeight: 48, borderRadius: 12, alignItems: 'center' },
  buttonText: { color: '#FFFFFF', fontSize: 15, fontWeight: '600' },
  secondary: { backgroundColor: '#E8EDE5' }, secondaryText: { color: '#345448' },
  disabled: { opacity: 0.5 }, history: { borderTopWidth: 1, borderColor: '#DADFD5', paddingVertical: 16, gap: 5 },
  error: { color: '#97382D', padding: 12, lineHeight: 22 }, footer: { color: '#626B61', textAlign: 'center', paddingVertical: 24 },
});
