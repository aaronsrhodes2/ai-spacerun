# Watchdog for stuck modifier keys and mouse buttons (Windows). Runs forever, hidden, from a logon scheduled task.
# Every second it checks Ctrl, Shift, Alt, Win and the three mouse buttons. If one reads as down continuously for longer than its limit,
# it sends the matching key-up / button-up and logs what was stuck, for how long, which window had focus, and how long ago the last real input was
# (so a pattern, such as a particular app or a wake from sleep, shows up in the log). A normal press, even a long Ctrl-drag, stays under the limits.
# Log: watch-stuck-input.log next to this script.
param([int]$ModifierLimit = 10, [int]$MouseLimit = 40, [int]$IntervalMs = 1000)
Add-Type @"
using System; using System.Runtime.InteropServices; using System.Text;
public class Stuck {
  [DllImport("user32.dll")] public static extern short GetAsyncKeyState(int vk);
  [DllImport("user32.dll")] public static extern void keybd_event(byte vk, byte scan, uint flags, UIntPtr extra);
  [DllImport("user32.dll")] public static extern void mouse_event(uint flags, int dx, int dy, uint data, UIntPtr extra);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  [StructLayout(LayoutKind.Sequential)] public struct LII { public uint cb; public uint time; }
  [DllImport("user32.dll")] public static extern bool GetLastInputInfo(ref LII p);
  public static double IdleSeconds() { LII l = new LII(); l.cb = (uint)Marshal.SizeOf(l); GetLastInputInfo(ref l); return ((uint)Environment.TickCount - l.time) / 1000.0; }
  public static string Foreground() { uint pid; GetWindowThreadProcessId(GetForegroundWindow(), out pid); try { return System.Diagnostics.Process.GetProcessById((int)pid).ProcessName; } catch { return "?"; } }
}
"@
$log = Join-Path $PSScriptRoot 'watch-stuck-input.log'
# name -> vk, kind (key/mouse), up flag for mouse_event, limit
$watch = @(
  @{ n = 'LCtrl'; vk = 0xA2; k = 'key'; lim = $ModifierLimit }, @{ n = 'RCtrl'; vk = 0xA3; k = 'key'; lim = $ModifierLimit },
  @{ n = 'LShift'; vk = 0xA0; k = 'key'; lim = $ModifierLimit }, @{ n = 'RShift'; vk = 0xA1; k = 'key'; lim = $ModifierLimit },
  @{ n = 'LAlt'; vk = 0xA4; k = 'key'; lim = $ModifierLimit }, @{ n = 'RAlt'; vk = 0xA5; k = 'key'; lim = $ModifierLimit },
  @{ n = 'LWin'; vk = 0x5B; k = 'key'; lim = $ModifierLimit }, @{ n = 'RWin'; vk = 0x5C; k = 'key'; lim = $ModifierLimit },
  @{ n = 'MouseLeft'; vk = 0x01; k = 'mouse'; up = 0x0004; lim = $MouseLimit },
  @{ n = 'MouseRight'; vk = 0x02; k = 'mouse'; up = 0x0010; lim = $MouseLimit },
  @{ n = 'MouseMiddle'; vk = 0x04; k = 'mouse'; up = 0x0040; lim = $MouseLimit }
)
$since = @{}
Add-Content -Path $log -Value ("{0}  watchdog started (modifiers {1}s, mouse {2}s)" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $ModifierLimit, $MouseLimit)
while ($true) {
  foreach ($w in $watch) {
    $down = ([Stuck]::GetAsyncKeyState($w.vk) -band 0x8000) -ne 0
    if (-not $down) { $since.Remove($w.n); continue }
    if (-not $since.ContainsKey($w.n)) { $since[$w.n] = Get-Date; continue }
    $held = ((Get-Date) - $since[$w.n]).TotalSeconds
    if ($held -ge $w.lim) {
      if ($w.k -eq 'key') { [Stuck]::keybd_event([byte]$w.vk, 0, 0x2, [UIntPtr]::Zero) } else { [Stuck]::mouse_event($w.up, 0, 0, 0, [UIntPtr]::Zero) }
      Add-Content -Path $log -Value ("{0}  released stuck {1} after {2:N0}s; focus={3}; idle={4:N0}s" -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $w.n, $held, [Stuck]::Foreground(), [Stuck]::IdleSeconds())
      $since.Remove($w.n)
    }
  }
  Start-Sleep -Milliseconds $IntervalMs
}
