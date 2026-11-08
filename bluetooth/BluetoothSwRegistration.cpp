// SPDX-License-Identifier: Apache-2.0
// Register the branch-native Bluetooth software module from the QTI HAL loader.
#define LOG_TAG "FroggerBluetoothAudio"
#include <android-base/logging.h>
#include <android/binder_manager.h>
#include <core-impl/Module.h>
#include <memory>
#include <mutex>
#include <string>

using aidl::android::hardware::audio::core::Module;

extern "C" int32_t registerIModuleBluetoothSWQti() {
    static std::mutex lock;
    static std::shared_ptr<Module> module;
    std::lock_guard<std::mutex> guard(lock);
    if (module) return STATUS_OK;
    const std::string name = std::string(Module::descriptor) + "/bluetooth";
    // The normal AOSP registration path may already have created this service.
    ndk::SpAIBinder existing(AServiceManager_checkService(name.c_str()));
    if (existing.get() != nullptr) return STATUS_OK;
    // A null configuration selects the complete built-in Bluetooth ports/routes.
    auto instance = Module::createInstance(Module::Type::BLUETOOTH,
                                          std::unique_ptr<Module::Configuration>{});
    if (!instance) {
        LOG(ERROR) << "Failed to create the Bluetooth software audio module";
        return STATUS_NO_MEMORY;
    }
    const binder_status_t status =
            AServiceManager_addService(instance->asBinder().get(), name.c_str());
    if (status == STATUS_OK) module = std::move(instance);
    else LOG(ERROR) << "Failed to register " << name << ": status=" << status
                    << ", declared=" << AServiceManager_isDeclared(name.c_str());
    return status;
}
