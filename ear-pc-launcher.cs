// ear-pc-launcher.cs — double-click launcher for patched ear (PC) + Ear (3)
// Does exactly what ear3_v8_override.py does at launch time:
//   kill zombie backends (any folder), kill electron, free port 17079,
//   wipe %APPDATA%\electron, start `py -3.11 main.pyc` hidden from exe's folder.
// Backend console goes to ear-pc.log. Errors -> message box.
// Build: run build_launcher.bat (uses Windows built-in csc.exe).

using System;
using System.Diagnostics;
using System.IO;
using System.Management;
using System.Threading;
using System.Windows.Forms;

class Launcher
{
    [STAThread]
    static void Main()
    {
        string root = AppDomain.CurrentDomain.BaseDirectory;
        Directory.SetCurrentDirectory(root);

        KillByCmdline("main.pyc");
        KillByName("electron");
        KillPortOwner(17079);
        TryDeleteDir(Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "electron"));

        if (!File.Exists(Path.Combine(root, "main.pyc")))
        {
            MessageBox.Show("main.pyc not found next to ear-pc.exe.\n" +
                            "Put ear-pc.exe in the ear-pc folder.", "ear (PC)");
            return;
        }

        string log = Path.Combine(root, "ear-pc.log");
        ProcessStartInfo psi = new ProcessStartInfo("py", "-3.11 main.pyc");
        psi.WorkingDirectory = root;
        psi.UseShellExecute = false;
        psi.CreateNoWindow = true;
        psi.RedirectStandardOutput = true;
        psi.RedirectStandardError = true;

        Process p;
        StreamWriter sw;
        try
        {
            sw = new StreamWriter(log, false);
            sw.AutoFlush = true;
            p = Process.Start(psi);
        }
        catch (Exception ex)
        {
            MessageBox.Show("Failed to start backend: " + ex.Message +
                            "\n\nIs Python launcher (py) installed?", "ear (PC)");
            return;
        }

        p.OutputDataReceived += delegate(object s, DataReceivedEventArgs e)
        { if (e.Data != null) { try { sw.WriteLine(e.Data); } catch { } } };
        p.ErrorDataReceived += delegate(object s, DataReceivedEventArgs e)
        { if (e.Data != null) { try { sw.WriteLine(e.Data); } catch { } } };
        p.BeginOutputReadLine();
        p.BeginErrorReadLine();

        Thread.Sleep(5000);
        if (p.HasExited)
        {
            string tail = "";
            try
            {
                string[] lines = File.ReadAllLines(log);
                int start = Math.Max(0, lines.Length - 12);
                for (int i = start; i < lines.Length; i++)
                    tail += lines[i] + "\n";
            }
            catch { }
            MessageBox.Show("Backend exited immediately.\n\n" + tail +
                            "\nFull log: ear-pc.log", "ear (PC)");
            return;
        }

        // stay resident (hidden) to keep log streaming until app closes
        p.WaitForExit();
        try { sw.Close(); } catch { }
    }

    static void KillByCmdline(string needle)
    {
        try
        {
            ManagementObjectSearcher s = new ManagementObjectSearcher(
                "SELECT ProcessId, CommandLine FROM Win32_Process " +
                "WHERE CommandLine LIKE '%" + needle + "%'");
            foreach (ManagementObject mo in s.Get())
            {
                try
                {
                    int pid = Convert.ToInt32(mo["ProcessId"]);
                    if (pid != Process.GetCurrentProcess().Id)
                        Process.GetProcessById(pid).Kill();
                }
                catch { }
            }
        }
        catch { }
    }

    static void KillByName(string name)
    {
        try
        {
            foreach (Process p in Process.GetProcessesByName(name))
            {
                try
                {
                    if (p.Id != Process.GetCurrentProcess().Id) p.Kill();
                }
                catch { }
            }
        }
        catch { }
    }

    static void KillPortOwner(int port)
    {
        try
        {
            ProcessStartInfo psi = new ProcessStartInfo("netstat", "-ano");
            psi.UseShellExecute = false;
            psi.CreateNoWindow = true;
            psi.RedirectStandardOutput = true;
            Process np = Process.Start(psi);
            string outp = np.StandardOutput.ReadToEnd();
            np.WaitForExit();
            string token = ":" + port.ToString() + " ";
            foreach (string line in outp.Split('\n'))
            {
                if (line.Contains(token) && line.Contains("LISTENING"))
                {
                    string[] parts = line.Trim().Split(
                        new char[] { ' ' },
                        StringSplitOptions.RemoveEmptyEntries);
                    int pid;
                    if (parts.Length > 0 &&
                        int.TryParse(parts[parts.Length - 1], out pid))
                    {
                        try
                        {
                            if (pid != Process.GetCurrentProcess().Id)
                                Process.GetProcessById(pid).Kill();
                        }
                        catch { }
                    }
                }
            }
        }
        catch { }
    }

    static void TryDeleteDir(string dir)
    {
        try { if (Directory.Exists(dir)) Directory.Delete(dir, true); }
        catch { }
    }
}
