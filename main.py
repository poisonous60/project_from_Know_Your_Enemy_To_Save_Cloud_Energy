import time
from typing import Dict, List, Tuple, Optional, NamedTuple
import unittest # 테스트를 위해 추가

# ADT에서 정의한 타입 별칭 (Python 타입 힌트용)
GPUt_ype = str
ServiceID = str
ClockMHz = int
PowerWatts = float
RPS = float
Timestamp = float # time.time() 사용

# ClockPerformanceData: (RPS, PowerWatts) 튜플
ClockPerformanceData = Tuple[RPS, PowerWatts]

# ServiceClockPerformanceMap: Dict[ClockMHz, ClockPerformanceData]
ServiceClockPerformanceMap = Dict[ClockMHz, ClockPerformanceData]

class OptimalValues(NamedTuple):
    optimal_clock_mhz: ClockMHz
    R_ij_rps_at_optimal_clock: RPS
    P_ij_dynamic_watts_at_optimal_clock: PowerWatts
    total_active_power_at_optimal_clock_watts: PowerWatts
    efficiency_at_optimal_clock: float

class GPUProfile:
    def __init__(self, idle_power: PowerWatts, supported_clocks: List[ClockMHz]):
        self.idle_power: PowerWatts = idle_power
        self.supported_clocks: List[ClockMHz] = list(supported_clocks) # Ensure it's a mutable list copy
        self.service_measurements_map: Dict[ServiceID, ServiceClockPerformanceMap] = {}
        self.last_general_update_timestamp: Timestamp = time.time()
        self.last_service_update_timestamps: Dict[ServiceID, Timestamp] = {} # Corrected typo from __

    def __repr__(self):
        return (f"GPUProfile(idle_power={self.idle_power}, "
                f"supported_clocks={len(self.supported_clocks)}, "
                f"services_profiled={len(self.service_measurements_map)})")

class GPUProfileCollection:
    """
    ADT GPUProfileCollection is
    object: <GPU_type, GPUProfile> 쌍으로 구성된 유한 집합
    """
    def __init__(self):
        # 시간 복잡도: O(1)
        # 공간 복잡도: O(1) 초기
        self._profiles: Dict[GPUt_ype, GPUProfile] = {}

    def add_gpu(self, gpu_id: GPUt_ype, initial_idle_power: PowerWatts, initial_supported_clocks: List[ClockMHz]) -> None:
        """
        2. AddGPU(gpc, gpu_id, initial_idle_power, initial_supported_clocks)
        시간 복잡도: O(1) 평균 (딕셔너리 삽입)
        공간 복잡도: 새로운 GPUProfile 객체 생성에 필요한 공간 추가
        """
        if gpu_id in self._profiles:
            raise ValueError(f"GPU ID {gpu_id} already exists in the collection.")
        self._profiles[gpu_id] = GPUProfile(initial_idle_power, initial_supported_clocks)
        # print(f"Added GPU: {gpu_id}") # 테스트 중에는 print문 주석 처리 가능

    def update_gpu_idle_power(self, gpu_id: GPUt_ype, new_idle_power: PowerWatts) -> None:
        """
        3. UpdateGPUIdlePower(gpc, gpu_id, new_idle_power)
        시간 복잡도: O(1) 평균 (딕셔너리 조회 및 업데이트)
        """
        if gpu_id not in self._profiles:
            raise KeyError(f"GPU ID {gpu_id} not found.")
        self._profiles[gpu_id].idle_power = new_idle_power
        self._profiles[gpu_id].last_general_update_timestamp = time.time()
        # print(f"Updated idle power for GPU {gpu_id} to {new_idle_power}W")

    def get_gpu_idle_power(self, gpu_id: GPUt_ype) -> PowerWatts:
        """
        4. PowerWatts GetGPUIdlePower(gpc, gpu_id)
        시간 복잡도: O(1) 평균 (딕셔너리 조회)
        """
        if gpu_id not in self._profiles:
            raise KeyError(f"GPU ID {gpu_id} not found.")
        return self._profiles[gpu_id].idle_power

    def add_or_update_service_clock_measurement(
        self, gpu_id: GPUt_ype, svc_id: ServiceID, clk: ClockMHz,
        measured_rps: RPS, measured_total_active_power: PowerWatts
    ) -> None:
        """
        5. AddOrUpdateServiceClockMeasurement(...)
        시간 복잡도: O(1) 평균 (중첩된 딕셔너리 조회 및 삽입/갱신)
        """
        if gpu_id not in self._profiles:
            raise KeyError(f"GPU ID {gpu_id} not found.")
        
        gpu_profile = self._profiles[gpu_id]
        if svc_id not in gpu_profile.service_measurements_map:
            gpu_profile.service_measurements_map[svc_id] = {}
        
        gpu_profile.service_measurements_map[svc_id][clk] = (measured_rps, measured_total_active_power)
        gpu_profile.last_service_update_timestamps[svc_id] = time.time()
        # print(f"Updated measurement for GPU {gpu_id}, Service {svc_id}, Clock {clk}MHz: RPS={measured_rps}, Power={measured_total_active_power}W")

    def calculate_and_get_optimal_energy_settings(self, gpu_id: GPUt_ype, svc_id: ServiceID) -> Optional[OptimalValues]:
        """
        6. OptimalValues CalculateAndGetOptimalEnergySettings(gpc, gpu_id, svc_id)
        시간 복잡도: O(C_s) 여기서 C_s는 해당 서비스/GPU에 대해 프로파일링된 클럭의 수.
        """
        if not self.is_service_measurements_exist_for_gpu(gpu_id, svc_id):
            # print(f"Warning: No measurements found for GPU {gpu_id} and Service {svc_id} to calculate optimal settings.")
            return None

        gpu_profile = self._profiles[gpu_id]
        idle_power = gpu_profile.idle_power
        service_clock_perf_map = gpu_profile.service_measurements_map[svc_id]

        if not service_clock_perf_map:
            # print(f"Warning: Measurement map is empty for GPU {gpu_id}, Service {svc_id}.")
            return None

        best_efficiency = -1.0
        optimal_settings: Optional[OptimalValues] = None

        for clk, (rps, total_active_power) in service_clock_perf_map.items():
            dynamic_power = total_active_power - idle_power
            if rps <= 0 or dynamic_power <= 0: 
                efficiency = 0.0 
            else:
                efficiency = rps / dynamic_power
            
            if efficiency > best_efficiency:
                best_efficiency = efficiency
                optimal_settings = OptimalValues(
                    optimal_clock_mhz=clk,
                    R_ij_rps_at_optimal_clock=rps,
                    P_ij_dynamic_watts_at_optimal_clock=dynamic_power,
                    total_active_power_at_optimal_clock_watts=total_active_power,
                    efficiency_at_optimal_clock=efficiency
                )
        
        # if optimal_settings:
        #      print(f"Optimal settings for GPU {gpu_id}, Service {svc_id}: Clock={optimal_settings.optimal_clock_mhz}MHz, Efficiency={optimal_settings.efficiency_at_optimal_clock:.2f} RPS/W_dynamic")
        # else:
        #     print(f"Could not determine optimal settings for GPU {gpu_id}, Service {svc_id} (e.g. all dynamic power <=0 or rps <=0).")
        return optimal_settings

    def get_service_clock_measurement(self, gpu_id: GPUt_ype, svc_id: ServiceID, clk: ClockMHz) -> Optional[ClockPerformanceData]:
        """
        7. ClockPerformanceData GetServiceClockMeasurement(...)
        시간 복잡도: O(1) 평균 (중첩된 딕셔너리 조회)
        """
        if not self.is_service_measurements_exist_for_gpu(gpu_id, svc_id):
            return None
        service_map = self._profiles[gpu_id].service_measurements_map[svc_id]
        return service_map.get(clk)

    def get_all_service_clock_measurements(self, gpu_id: GPUt_ype, svc_id: ServiceID) -> Optional[ServiceClockPerformanceMap]:
        """
        8. Map<ClockMHz, ClockPerformanceData> GetAllServiceClockMeasurement(...)
        시간 복잡도: O(1) 평균 (딕셔너리 참조 반환). 얕은 복사본 반환 시 O(C_s).
        """
        if not self.is_service_measurements_exist_for_gpu(gpu_id, svc_id):
            return None
        return self._profiles[gpu_id].service_measurements_map[svc_id]


    def get_supported_clocks(self, gpu_id: GPUt_ype) -> List[ClockMHz]:
        """
        9. List<ClockMHz> GetSupportedClocks(...)
        시간 복잡도: O(1) (리스트 참조 반환). 얕은 복사본 반환 시 O(L) 여기서 L은 리스트 길이.
        """
        if gpu_id not in self._profiles:
            raise KeyError(f"GPU ID {gpu_id} not found.")
        return self._profiles[gpu_id].supported_clocks

    def is_gpu_exist(self, gpu_id: GPUt_ype) -> bool:
        """
        10. Boolean IsGPUExist(...)
        시간 복잡도: O(1) 평균
        """
        return gpu_id in self._profiles

    def is_service_measurements_exist_for_gpu(self, gpu_id: GPUt_ype, svc_id: ServiceID) -> bool:
        """
        11. Boolean IsServiceMeasurementsExistForGPU(...)
        시간 복잡도: O(1) 평균
        """
        if not self.is_gpu_exist(gpu_id):
            return False
        return svc_id in self._profiles[gpu_id].service_measurements_map
    
    # 공간 복잡도에 대한 종합적 분석:
    # N_g: GPU의 수
    # L_c_avg: GPU당 supported_clocks 리스트의 평균 길이
    # S_avg: GPU당 평균적으로 프로파일링된 서비스의 수
    # C_avg: 서비스당 평균적으로 프로파일링된 클럭의 수 (즉, ServiceClockPerformanceMap의 평균 크기)
    # 전체 공간 복잡도: O(N_g * (1 + L_c_avg + S_avg * (1 + C_avg))))
    # 각 GPUProfile 객체는 고정된 크기의 기본 정보(idle_power, last_general_update_timestamp)와
    # supported_clocks 리스트 (평균 L_c_avg),
    # last_service_update_timestamps 딕셔너리 (평균 S_avg 항목),
    # service_measurements_map 딕셔너리 (평균 S_avg 서비스 항목)를 가짐.
    # 각 service_measurements_map의 값인 ServiceClockPerformanceMap은 평균 C_avg개의 클럭 측정치(RPS, PowerWatts 튜플)를 가짐.

class TestGPUProfileCollection(unittest.TestCase):
    def setUp(self):
        self.gpc = GPUProfileCollection()
        self.gpu1_id = "Tesla_V100"
        self.gpu1_idle_power = 50.0
        self.gpu1_supported_clocks = [1000, 1200, 1350]

        self.svc1_id = "ResNet50"
        self.svc2_id = "BERT"

    def test_01_add_and_check_gpu(self):
        self.assertFalse(self.gpc.is_gpu_exist(self.gpu1_id))
        self.gpc.add_gpu(self.gpu1_id, self.gpu1_idle_power, self.gpu1_supported_clocks)
        self.assertTrue(self.gpc.is_gpu_exist(self.gpu1_id))
        with self.assertRaises(ValueError):
            self.gpc.add_gpu(self.gpu1_id, self.gpu1_idle_power, self.gpu1_supported_clocks)

    def test_02_update_and_get_idle_power(self):
        self.gpc.add_gpu(self.gpu1_id, self.gpu1_idle_power, self.gpu1_supported_clocks)
        self.assertEqual(self.gpc.get_gpu_idle_power(self.gpu1_id), self.gpu1_idle_power)
        
        new_idle_power = 55.0
        self.gpc.update_gpu_idle_power(self.gpu1_id, new_idle_power)
        self.assertEqual(self.gpc.get_gpu_idle_power(self.gpu1_id), new_idle_power)
        
        with self.assertRaises(KeyError):
            self.gpc.get_gpu_idle_power("NonExistentGPU")

    def test_03_add_and_get_service_measurements(self):
        self.gpc.add_gpu(self.gpu1_id, self.gpu1_idle_power, self.gpu1_supported_clocks)
        self.assertFalse(self.gpc.is_service_measurements_exist_for_gpu(self.gpu1_id, self.svc1_id))

        self.gpc.add_or_update_service_clock_measurement(self.gpu1_id, self.svc1_id, 1000, 800, 180)
        self.gpc.add_or_update_service_clock_measurement(self.gpu1_id, self.svc1_id, 1200, 950, 220)
        self.gpc.add_or_update_service_clock_measurement(self.gpu1_id, self.svc1_id, 1350, 1050, 270)

        self.assertTrue(self.gpc.is_service_measurements_exist_for_gpu(self.gpu1_id, self.svc1_id))
        
        measurement = self.gpc.get_service_clock_measurement(self.gpu1_id, self.svc1_id, 1200)
        self.assertIsNotNone(measurement)
        self.assertEqual(measurement, (950, 220))
        
        self.assertIsNone(self.gpc.get_service_clock_measurement(self.gpu1_id, self.svc1_id, 900)) # Non-existent clock

        all_measurements = self.gpc.get_all_service_clock_measurements(self.gpu1_id, self.svc1_id)
        self.assertIsNotNone(all_measurements)
        self.assertEqual(len(all_measurements), 3)
        self.assertEqual(all_measurements[1000], (800, 180))
        
        # Test non-existent service
        self.assertIsNone(self.gpc.get_all_service_clock_measurements(self.gpu1_id, self.svc2_id))


    def test_04_calculate_optimal_settings(self):
        self.gpc.add_gpu(self.gpu1_id, self.gpu1_idle_power, self.gpu1_supported_clocks)
        
        self.assertIsNone(self.gpc.calculate_and_get_optimal_energy_settings(self.gpu1_id, self.svc1_id)) # No data

        # Data for svc1
        self.gpc.add_or_update_service_clock_measurement(self.gpu1_id, self.svc1_id, 1000, 800, 180) # eff=6.15 (dyn_p=130)
        self.gpc.add_or_update_service_clock_measurement(self.gpu1_id, self.svc1_id, 1200, 950, 220) # eff=5.58 (dyn_p=170)
        self.gpc.add_or_update_service_clock_measurement(self.gpu1_id, self.svc1_id, 1350, 1050, 270)# eff=4.77 (dyn_p=220)

        optimal_svc1 = self.gpc.calculate_and_get_optimal_energy_settings(self.gpu1_id, self.svc1_id)
        self.assertIsNotNone(optimal_svc1)
        self.assertEqual(optimal_svc1.optimal_clock_mhz, 1000)
        self.assertEqual(optimal_svc1.R_ij_rps_at_optimal_clock, 800)
        self.assertEqual(optimal_svc1.P_ij_dynamic_watts_at_optimal_clock, 180 - self.gpu1_idle_power)
        self.assertEqual(optimal_svc1.total_active_power_at_optimal_clock_watts, 180)
        self.assertAlmostEqual(optimal_svc1.efficiency_at_optimal_clock, 800 / (180 - self.gpu1_idle_power), places=2)

        # Data for svc2 - different optimal point
        self.gpc.add_or_update_service_clock_measurement(self.gpu1_id, self.svc2_id, 1000, 50, 100)  # eff=1.0 (dyn_p=50)
        self.gpc.add_or_update_service_clock_measurement(self.gpu1_id, self.svc2_id, 1200, 100, 160) # eff=0.90 (dyn_p=110)
        self.gpc.add_or_update_service_clock_measurement(self.gpu1_id, self.svc2_id, 1350, 120, 180) # eff=0.92 (dyn_p=130)
        
        # Re-add with better efficiency for 1200 to change optimal
        self.gpc.add_or_update_service_clock_measurement(self.gpu1_id, self.svc2_id, 1200, 150, 170) # eff=1.25 (dyn_p=120)


        optimal_svc2 = self.gpc.calculate_and_get_optimal_energy_settings(self.gpu1_id, self.svc2_id)
        self.assertIsNotNone(optimal_svc2)
        self.assertEqual(optimal_svc2.optimal_clock_mhz, 1200)
        self.assertEqual(optimal_svc2.R_ij_rps_at_optimal_clock, 150)
        self.assertEqual(optimal_svc2.P_ij_dynamic_watts_at_optimal_clock, 170 - self.gpu1_idle_power) # 120
        self.assertAlmostEqual(optimal_svc2.efficiency_at_optimal_clock, 150 / (170 - self.gpu1_idle_power), places=2)

        # Test case where all dynamic power is <= 0 or rps is <=0
        # GPU_Test를 먼저 추가합니다.
        self.gpc.add_gpu("GPU_Test", 50.0, [1000, 1100]) # supported_clocks에 테스트할 클럭 포함
        
        # 이제 GPU_Test에 대한 측정치를 추가합니다. (svc1에 대한 측정)
        self.gpc.add_or_update_service_clock_measurement("GPU_Test", self.svc1_id, 1000, 10, 40) # dyn_p = 10 - 50 = -40
        optimal_invalid = self.gpc.calculate_and_get_optimal_energy_settings("GPU_Test", self.svc1_id)
        # 위의 calculate_and_get_optimal_energy_settings 수정 제안에 따라 None 또는 efficiency 0인 값 확인
        if optimal_invalid is not None and optimal_invalid.efficiency_at_optimal_clock > 0:
            self.fail("Optimal settings found for invalid data (negative dynamic power)")
        elif optimal_invalid is None : # 유효한 측정치가 없어서 None이 반환된 경우 OK
            pass
        elif optimal_invalid.efficiency_at_optimal_clock == 0.0: # 효율이 0으로 계산된 경우 OK
            pass


        # svc2에 대한 측정 (RPS가 0)
        self.gpc.add_or_update_service_clock_measurement("GPU_Test", self.svc2_id, 1100, 0, 60) # RPS is 0
        optimal_invalid_rps = self.gpc.calculate_and_get_optimal_energy_settings("GPU_Test", self.svc2_id)
        if optimal_invalid_rps is not None and optimal_invalid_rps.efficiency_at_optimal_clock > 0:
            self.fail("Optimal settings found for invalid data (zero RPS)")
        elif optimal_invalid_rps is None :
            pass
        elif optimal_invalid_rps.efficiency_at_optimal_clock == 0.0:
            pass


    def test_05_get_supported_clocks(self):
        self.gpc.add_gpu(self.gpu1_id, self.gpu1_idle_power, self.gpu1_supported_clocks)
        clocks = self.gpc.get_supported_clocks(self.gpu1_id)
        self.assertEqual(clocks, self.gpu1_supported_clocks)
        # Test that it returns a copy if we want to enforce immutability (current impl returns ref)
        # clocks.append(2000) 
        # self.assertNotEqual(self.gpc.get_supported_clocks(self.gpu1_id), clocks) # This would fail if it's a ref

# To run the tests when the script is executed:
# Note: For environments like Jupyter/Colab, unittest.main() needs special handling.
# If running directly as a script (e.g., python your_script_name.py), use:
if __name__ == '__main__':
   unittest.main()

# # For Colab/Jupyter, this is a common way:
# if __name__ == '__main__':
#     suite = unittest.TestSuite()
#     suite.addTest(unittest.makeSuite(TestGPUProfileCollection))
#     runner = unittest.TextTestRunner()
#     print("Running ADT GPUProfileCollection Tests:")
#     runner.run(suite)