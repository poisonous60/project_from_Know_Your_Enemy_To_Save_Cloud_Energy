# project_from_Know_Your_Enemy_To_Save_Cloud_Energy
https://github.com/EMDC-OS/power-aware-triton
2025 1학기 자료구조개론 강의 프로젝트 과제
```python
﻿typedef struct GPUProfile {  
    PowerWatts idle_power : 유휴 상태 소비전력
    List<ClockMHz> supported_clocks : GPU의 DVFS 기능으로 바꿀 수 있는 클럭
    Map<ServiceID, ServiceClockPerformanceMap> service_measurements_map : 모델, GPU 종류별 클럭에 따른 처리율과 소모 전력
    time last_general_update_timestamp : 마지막 갱신 시간
    Map<ServiceID, time> last_service__update_timestamps : 서비스별 service_measurements_map 갱신 시간
}
typedef Map<ClockMHz, ClockPerformanceData> ServiceClockPerformanceMap
typedef tuple<RPS, PowerWatts> ClockPerformanceData

typedef struct OptimalValues {  
    ClockMHz optimal_clock_mhz : 사전 클러스터 구성에 사용되는 최적 클럭
    RPS R_ij : 최적 클럭에 대한 처리율
    PowerWatts P_ij : 최적 클럭에 대한 동적 전력 소모량(활성 전력 - 유휴 전력)
    PowerWatts total_active_power_at_optimal_clock_watts : 최적 클럭에서 총 활성 전력
    float efficiency_at_optimal_clock : 최적 클럭에서 에너지 효율성 값
}
ADT GPUProfileCollection is
object: <GPU_type, GPUProfile> 쌍으로 구성된 유한 집합
function: 모든 gpc ∈GPUProfileCollection, gpu_id ∈GPU_type, clk ∈ClockMHz, power ∈PowerWatts, clock_list ∈List<ClockMHz>, rps_val ∈ RPS, svc_id ∈ ServiceID 에 대하여

1. GPUProfileCollection CreateGPUProfileCollection() : 
  비어있는 GPUProfileCollection을 생성하여 반환한다.
2. void AddGPU(gpc, gpu_id, initial_idle_power, initial_supported_clocks) :
  gpc에 gpu_id가 존재하지 않을 때, gpu_id를 키로 하는 새로운 GPUProfile을 gpc에 추가한다. 
3. void UpdateGPUIdlePower(gpc, gpu_id, new_idle_power) :
  gpc에 gpu_id가 존재할 때, idle_power = new_idle_power를 갱신하고 last_general_update_timestamp를 현재 시간으로 변경한다.
4. PowerWatts GetGPUIdlePower(gpc, gpu_id) : 
  gpc에 gpu_id가 존재할 때, gpc 내 gpu_id에 해당하는 GPUProfile의 idle_power를 반환한다.
5. void AddOrUpdateServiceClockMeasurement(gpc, gpu_id, svc_id, clk, measured_rps, measured_total_active_power) : 
  gpu_id가 gpc에 존재할 때, gpc 내 gpu_id의 GPUProfile에서, service_measurements_map 내 svc_id에 해당하는 ServiceClockPerformanceMap 객체를 (없으면 새로 생성하여) 가져온다. 해당 맵에 clk를 키로 하여 (measured_rps, measured_total_active_power) 쌍으로 구성된 ClockPerformanceData를 저장하거나 갱신하고 last_service_update_timestamps[svc_id]를 현재 시간으로 변경한다.
6. OptimalValues CalculateAndGetOptimalEnergySettings(gpc, gpu_id, svc_id) : 
  1. 피크 요청량과 GPU 소비 전력에 따른 서비스 클러스터에 대한 GPU 노드 할당, 2. 요청률에 따른 서비스 클러스터 내 활성 GPU 노드 수 스케일링에서 사용되는 최적 클럭, Rij, Pij를 반환한다. 
  gpu_id가 gpc에 존재하고, 해당 GPUProfile내 service_measurements_map에 svc_id가 존재할 때, service_measurements_map 맵의 모든 클럭 측정치에 대해 에너지 효율성 (RPS / (total_active_power_watts- idle_power))을 계산한다. 가장 높은 효율성을 내는 클럭과 그때의 Rij​(처리율), Pij(동적 전력), 총 활성 전력과 효율성(로깅 및 분석용) 값을 포함하는 OptimalValues객체를 계산하여 반환한다.
7. ClockPerformanceData GetServiceClockMeasurement(gpc, gpu_id, svc_id, clk):
  gpu_id가 gpc에 존재하고, 해당 GPUProfile 내 service_measurements_map에 svc_id가 존재하며, 해당 서비스의 ServiceClockPerformanceMap에 clk가 존재할 때, 특정 서비스, GPU, 클럭에서의 측정된 throughput_rps와 total_active_power_watts를 담은 ClockPerformanceData객체를 반환한다. (편의성 용 조회 기능)
8. Map<ClockMHz, ClockPerformanceData> GetAllServiceClockMeasurement(gpc, gpu_id, svc_id) : 
  gpu_id가 gpc에 존재하고, 해당 GPUProfile내 service_measurements_map에 svc_id가 존재할 때, gpc내 gpu_id, svc_id에 해당하는 ServiceClockPerformanceMap전체를 반환한다.
  반환된 Map은 3. GPU 노드 내 활성 GPU 수 스케일링, 4. 활성 GPU의 클럭 스케일링에서 사용하는 TimeToClock(그리고 이를 호출하는 Opt_Clock) 함수를 구현하는 데 사용된다.
9. List<ClockMHz> GetSupportedClocks(gpc, gpu_id) : 
  gpc에 gpu_id가 존재할 때, gpc 내 gpu_id에 해당하는 GPUProfile의 supported_clocks 리스트를 반환한다.
10. Boolean IsGPUExist(gpc, gpu_id) : 
  gpc 내에 gpu_id가 존재하면 True, 아니면 False를 반환한다.
11. Boolean IsServiceMeasurementsExistForGPU(gpc, gpu_id, svc_id) : 
  gpc 내 gpu_id에 해당하는 GPUProfile의 service_measurements_map에 svc_id가 존재하면 True, 아니면 False를 반환한다.
```
