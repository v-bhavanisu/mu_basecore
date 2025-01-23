/** @file
  Google Test mocks for UefiRuntimeServicesTableLib

  Copyright (c) 2022, Intel Corporation. All rights reserved.
  SPDX-License-Identifier: BSD-2-Clause-Patent
**/
#include <GoogleTest/Library/MockUefiRuntimeServicesTableLib.h>

MOCK_INTERFACE_DEFINITION (MockUefiRuntimeServicesTableLib);

MOCK_FUNCTION_DEFINITION (MockUefiRuntimeServicesTableLib, gRT_GetTime, 2, EFIAPI);
MOCK_FUNCTION_DEFINITION (MockUefiRuntimeServicesTableLib, gRT_SetTime, 1, EFIAPI);
MOCK_FUNCTION_DEFINITION (MockUefiRuntimeServicesTableLib, gRT_GetWakeupTime, 3, EFIAPI);
MOCK_FUNCTION_DEFINITION (MockUefiRuntimeServicesTableLib, gRT_SetWakeupTime, 2, EFIAPI);

MOCK_FUNCTION_DEFINITION (MockUefiRuntimeServicesTableLib, gRT_SetVirtualAddressMap, 4, EFIAPI);
MOCK_FUNCTION_DEFINITION (MockUefiRuntimeServicesTableLib, gRT_ConvertPointer, 2, EFIAPI);

MOCK_FUNCTION_DEFINITION (MockUefiRuntimeServicesTableLib, gRT_GetVariable, 5, EFIAPI);
MOCK_FUNCTION_DEFINITION (MockUefiRuntimeServicesTableLib, gRT_GetNextVariableName, 3, EFIAPI);
MOCK_FUNCTION_DEFINITION (MockUefiRuntimeServicesTableLib, gRT_SetVariable, 5, EFIAPI);

MOCK_FUNCTION_DEFINITION (MockUefiRuntimeServicesTableLib, gRT_GetNextHighMonotonicCount, 1, EFIAPI);
MOCK_FUNCTION_DEFINITION (MockUefiRuntimeServicesTableLib, gRT_ResetSystem, 4, EFIAPI);

MOCK_FUNCTION_DEFINITION (MockUefiRuntimeServicesTableLib, gRT_UpdateCapsule, 3, EFIAPI);
MOCK_FUNCTION_DEFINITION (MockUefiRuntimeServicesTableLib, gRT_QueryCapsuleCapabilities, 4, EFIAPI);

MOCK_FUNCTION_DEFINITION (MockUefiRuntimeServicesTableLib, gRT_QueryVariableInfo, 4, EFIAPI);

static EFI_RUNTIME_SERVICES  localRt = {
  { 0 },                          // EFI_TABLE_HEADER

  gRT_GetTime,                    // EFI_GET_TIME
  gRT_SetTime,                    // EFI_SET_TIME
  gRT_GetWakeupTime,              // EFI_GET_WAKEUP_TIME
  gRT_SetWakeupTime,              // EFI_SET_WAKEUP_TIME

  gRT_SetVirtualAddressMap,       // EFI_SET_VIRTUAL_ADDRESS_MAP
  gRT_ConvertPointer,             // EFI_CONVERT_POINTER

  gRT_GetVariable,                // EFI_GET_VARIABLE
  gRT_GetNextVariableName,        // EFI_GET_NEXT_VARIABLE_NAME
  gRT_SetVariable,                // EFI_SET_VARIABLE

  gRT_GetNextHighMonotonicCount,  // EFI_GET_NEXT_HIGH_MONO_COUNT
  gRT_ResetSystem,                // EFI_RESET_SYSTEM

  gRT_UpdateCapsule,              // EFI_UPDATE_CAPSULE
  gRT_QueryCapsuleCapabilities,   // EFI_QUERY_CAPSULE_CAPABILITIES

  gRT_QueryVariableInfo,          // EFI_QUERY_VARIABLE_INFO
};

extern "C" {
  EFI_RUNTIME_SERVICES  *gRT = &localRt;
}
