import ctypes
from ctypes import wintypes, byref, c_int, c_byte, c_bool, c_long, c_void_p, create_string_buffer, POINTER
import os
import sys
import threading
from datetime import datetime

# Global SDK lock to prevent multi-threaded crashes
sdk_lock = threading.Lock()

class BiometricConnector:
    def __init__(self, dll_dir=None):
        if dll_dir is None:
            dll_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'native')
        
        self.dll_dir = dll_dir
        self.h_comm = None
        self.h_sbxpc = None
        self.connected = False
        self.machine_number = 1

        self._ConnectTcpip = None
        self._Disconnect = None
        self._SetDeviceTime = None
        self._EnableDevice = None
        self._ReadAllUserID = None
        self._GetAllUserID = None
        self._GetUserName1 = None
        self._ReadAllGLogData = None
        self._ReadGeneralLogData = None
        self._GetAllGLogData = None
        self._GetSerialNumber = None

        self._oleaut32 = None
        if hasattr(ctypes, 'windll') and hasattr(ctypes.windll, 'oleaut32'):
            self._oleaut32 = ctypes.windll.oleaut32
            self._oleaut32.SysAllocString.restype = c_void_p
            self._oleaut32.SysAllocString.argtypes = [ctypes.c_wchar_p]
            self._oleaut32.SysFreeString.argtypes = [c_void_p]

        self._init_dlls()

    def _get_api(self, name):
        """Resolves function with or without underscore prefix from SBXPCDLL64.dll"""
        for n in ['_' + name, name]:
            if hasattr(self.h_sbxpc, n):
                return getattr(self.h_sbxpc, n)
        return None

    def _init_dlls(self):
        if sys.platform == 'win32' and hasattr(os, 'add_dll_directory'):
            try:
                os.add_dll_directory(self.dll_dir)
            except Exception as e:
                print(f"[Biometric] Warning adding DLL dir: {e}")

        comm_path = os.path.join(self.dll_dir, 'SBPCCOMM64.dll')
        sbxpc_path = os.path.join(self.dll_dir, 'SBXPCDLL64.dll')

        if not os.path.exists(sbxpc_path):
            print(f"[Biometric] DLL not found: {sbxpc_path}")
            return

        try:
            if os.path.exists(comm_path):
                self.h_comm = ctypes.WinDLL(comm_path)
            self.h_sbxpc = ctypes.WinDLL(sbxpc_path)
            self._setup_function_prototypes()
            print("[Biometric] 64-bit DLLs loaded successfully.")
        except Exception as e:
            print(f"[Biometric] Error loading DLLs: {e}")

    def _setup_function_prototypes(self):
        if not self.h_sbxpc:
            return

        # ConnectTcpip(dwMachineNumber, ref IntPtr lpszIPAddress, dwPort, dwPassWord)
        fn = self._get_api('ConnectTcpip')
        if fn:
            fn.restype = c_byte
            fn.argtypes = [c_long, POINTER(c_void_p), c_long, c_long]
            self._ConnectTcpip = fn

        # Disconnect(dwMachineNumber)
        fn = self._get_api('Disconnect')
        if fn:
            fn.restype = None
            fn.argtypes = [c_long]
            self._Disconnect = fn

        # SetDeviceTime(dwMachineNumber)
        fn = self._get_api('SetDeviceTime')
        if fn:
            fn.restype = c_byte
            fn.argtypes = [c_long]
            self._SetDeviceTime = fn

        # EnableDevice(dwMachineNumber, bFlag)
        fn = self._get_api('EnableDevice')
        if fn:
            fn.restype = c_byte
            fn.argtypes = [c_long, c_byte]
            self._EnableDevice = fn

        # ReadAllUserID(dwMachineNumber)
        fn = self._get_api('ReadAllUserID')
        if fn:
            fn.restype = c_byte
            fn.argtypes = [c_long]
            self._ReadAllUserID = fn

        # GetAllUserID(dwMachineNumber, dwEnrollNumber, dwEMachineNumber, dwBackupNumber, dwMachinePrivilege, dwEnable)
        fn = self._get_api('GetAllUserID')
        if fn:
            fn.restype = c_byte
            fn.argtypes = [
                c_long,
                POINTER(c_long),
                POINTER(c_long),
                POINTER(c_long),
                POINTER(c_long),
                POINTER(c_long)
            ]
            self._GetAllUserID = fn

        # GetUserName1(dwMachineNumber, dwEnrollNumber, out lpszUserName)
        fn = self._get_api('GetUserName1')
        if fn:
            fn.restype = c_byte
            fn.argtypes = [c_long, c_long, POINTER(c_void_p)]
            self._GetUserName1 = fn

        # ReadAllGLogData(dwMachineNumber)
        fn = self._get_api('ReadAllGLogData')
        if fn:
            fn.restype = c_byte
            fn.argtypes = [c_long]
            self._ReadAllGLogData = fn

        # ReadGeneralLogData(dwMachineNumber)
        fn = self._get_api('ReadGeneralLogData')
        if fn:
            fn.restype = c_byte
            fn.argtypes = [c_long]
            self._ReadGeneralLogData = fn

        # GetAllGLogData(dwMachineNumber, dwTMachineNumber, dwEnrollNumber, dwEMachineNumber, dwVerifyMode, dwYear, dwMonth, dwDay, dwHour, dwMinute, dwSecond)
        fn = self._get_api('GetAllGLogData')
        if fn:
            fn.restype = c_byte
            fn.argtypes = [
                c_long,
                POINTER(c_long),
                POINTER(c_long),
                POINTER(c_long),
                POINTER(c_long),
                POINTER(c_long),
                POINTER(c_long),
                POINTER(c_long),
                POINTER(c_long),
                POINTER(c_long),
                POINTER(c_long),
            ]
            self._GetAllGLogData = fn

        # GetSerialNumber(dwMachineNumber, ref lpszSerialNumber)
        fn = self._get_api('GetSerialNumber')
        if fn:
            fn.restype = c_byte
            fn.argtypes = [c_long, POINTER(c_void_p)]
            self._GetSerialNumber = fn

    def connect(self, ip="192.168.1.224", port=5005, machine_number=1, password=0):
        if not self.h_sbxpc or not self._ConnectTcpip:
            return False, "Hardware DLLs not initialized or API missing"

        with sdk_lock:
            try:
                ip_clean = str(ip).strip()
                mach_id = int(machine_number)
                port_num = int(port)
                pwd_num = int(password or 0)

                bstr_ip = self._oleaut32.SysAllocString(ip_clean)
                p_bstr = c_void_p(bstr_ip)
                self.machine_number = mach_id

                ret = self._ConnectTcpip(mach_id, byref(p_bstr), port_num, pwd_num)
                self._oleaut32.SysFreeString(bstr_ip)

                self.connected = (ret > 0)
                if self.connected:
                    # Auto-sync hardware RTC clock to host PC time
                    if self._SetDeviceTime:
                        try:
                            self._SetDeviceTime(self.machine_number)
                        except Exception as te:
                            print(f"[Biometric] Clock sync notice: {te}")
                    return True, f"Connected successfully to biometric hardware at {ip_clean}:{port_num}"
                return False, f"Failed to connect to biometric hardware at {ip_clean}:{port_num} (Machine ID: {mach_id})"
            except Exception as e:
                self.connected = False
                return False, str(e)

    def disconnect(self):
        if not self.connected or not self.h_sbxpc:
            return
        with sdk_lock:
            try:
                if self._Disconnect:
                    self._Disconnect(self.machine_number)
            except Exception as e:
                print(f"[Biometric] Disconnect error: {e}")
            finally:
                self.connected = False

    def sync_device_time(self):
        if not self.connected:
            return False, "Not connected"
        if not self._SetDeviceTime:
            return False, "SetDeviceTime API not available"
        with sdk_lock:
            try:
                res = self._SetDeviceTime(self.machine_number)
                return (res > 0), "Device time synchronized with host PC"
            except Exception as e:
                return False, str(e)

    def get_device_serial(self):
        """Reads device hardware serial number if available"""
        if not self.connected or not self._GetSerialNumber:
            return None
        with sdk_lock:
            try:
                empty_bstr = self._oleaut32.SysAllocString("")
                p_bstr = c_void_p(empty_bstr)
                ret = self._GetSerialNumber(self.machine_number, byref(p_bstr))
                serial = None
                if ret > 0 and p_bstr.value:
                    serial = ctypes.wstring_at(p_bstr.value).strip()
                self._oleaut32.SysFreeString(empty_bstr)
                return serial
            except Exception:
                pass
        return None

    def get_enrolled_workers(self):
        """
        Reads all enrolled workers and their IDs directly from the biometric device.
        Deduplicates multiple biometric templates (fingers, card, pin) per worker and fetches user names.
        Returns: (success: bool, message: str, workers: list)
        """
        if not self.connected:
            return False, "Not connected to biometric device", []
        if not self._ReadAllUserID or not self._GetAllUserID:
            return False, "Enrolled worker read APIs not available in DLL", []

        workers_map = {}
        with sdk_lock:
            try:
                # Temporarily lock terminal UI during data transmission
                if self._EnableDevice:
                    self._EnableDevice(self.machine_number, 0)

                read_ok = self._ReadAllUserID(self.machine_number)
                if read_ok <= 0:
                    if self._EnableDevice:
                        self._EnableDevice(self.machine_number, 1)
                    return True, "No enrolled workers found or device returned empty list", []

                dw_enroll = c_long()
                dw_emachine = c_long()
                dw_backup = c_long()
                dw_privilege = c_long()
                dw_enable = c_long()

                while self._GetAllUserID(
                    self.machine_number,
                    byref(dw_enroll),
                    byref(dw_emachine),
                    byref(dw_backup),
                    byref(dw_privilege),
                    byref(dw_enable)
                ) > 0:
                    enr = int(dw_enroll.value)
                    if enr <= 0:
                        continue

                    if enr not in workers_map:
                        workers_map[enr] = {
                            'enroll_number': enr,
                            'name': '',
                            'privilege': int(dw_privilege.value),
                            'enabled': bool(dw_enable.value),
                            'backup_numbers': [int(dw_backup.value)]
                        }
                    else:
                        workers_map[enr]['backup_numbers'].append(int(dw_backup.value))

                # Fetch user names via GetUserName1
                if self._GetUserName1:
                    for enr, w in workers_map.items():
                        try:
                            p_name = c_void_p()
                            ret_n = self._GetUserName1(self.machine_number, enr, byref(p_name))
                            if ret_n > 0 and p_name.value:
                                name_val = ctypes.wstring_at(p_name.value).strip()
                                if name_val:
                                    w['name'] = name_val
                        except Exception:
                            pass

                # Build final worker list, defaulting name if not stored on device
                worker_list = []
                for enr, w in sorted(workers_map.items()):
                    if not w['name']:
                        w['name'] = f"Worker #{enr}"
                    worker_list.append(w)

                if self._EnableDevice:
                    self._EnableDevice(self.machine_number, 1)

                return True, f"Successfully retrieved {len(worker_list)} enrolled worker(s) from device", worker_list

            except Exception as e:
                if self._EnableDevice:
                    try:
                        self._EnableDevice(self.machine_number, 1)
                    except Exception:
                        pass
                return False, f"Error reading enrolled workers: {e}", []

    def get_attendance_logs(self, full_sync=True):
        """
        Reads general attendance punch logs from the biometric device.
        Returns: (success: bool, message: str, logs: list)
        """
        if not self.connected:
            return False, "Not connected", []

        logs = []
        with sdk_lock:
            try:
                if self._EnableDevice:
                    self._EnableDevice(self.machine_number, 0)

                read_ok = 0
                if full_sync and self._ReadAllGLogData:
                    read_ok = self._ReadAllGLogData(self.machine_number)
                elif self._ReadGeneralLogData:
                    read_ok = self._ReadGeneralLogData(self.machine_number)

                if read_ok <= 0:
                    if self._EnableDevice:
                        self._EnableDevice(self.machine_number, 1)
                    return True, "No new logs or read returned false", []

                dw_tmach = c_long()
                dw_enroll = c_long()
                dw_emach = c_long()
                dw_verify = c_long()
                dw_year = c_long()
                dw_month = c_long()
                dw_day = c_long()
                dw_hour = c_long()
                dw_minute = c_long()
                dw_second = c_long()

                current_year = datetime.now().year

                while self._GetAllGLogData(
                    self.machine_number,
                    byref(dw_tmach),
                    byref(dw_enroll),
                    byref(dw_emach),
                    byref(dw_verify),
                    byref(dw_year),
                    byref(dw_month),
                    byref(dw_day),
                    byref(dw_hour),
                    byref(dw_minute),
                    byref(dw_second)
                ) > 0:
                    yr = dw_year.value
                    # Reject corrupt or uninitialized RTC years
                    if yr < 2024 or yr > current_year + 1:
                        continue

                    try:
                        timestamp = datetime(
                            yr, dw_month.value, dw_day.value,
                            dw_hour.value, dw_minute.value, dw_second.value
                        ).strftime('%Y-%m-%d %H:%M:%S')

                        # Determine in/out mode based on hour or verify mode
                        hr = dw_hour.value
                        in_out = 0 if hr < 13 else 1

                        logs.append({
                            'enroll_number': int(dw_enroll.value),
                            'verify_mode': int(dw_verify.value),
                            'in_out_mode': in_out,
                            'timestamp': timestamp
                        })
                    except ValueError:
                        continue

                if self._EnableDevice:
                    self._EnableDevice(self.machine_number, 1)

                return True, f"Successfully fetched {len(logs)} logs", logs
            except Exception as e:
                if self._EnableDevice:
                    try:
                        self._EnableDevice(self.machine_number, 1)
                    except Exception:
                        pass
                return False, str(e), []
