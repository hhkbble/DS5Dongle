cmake_minimum_required(VERSION 3.20)
project(ds5_hid_report_policy_tests LANGUAGES CXX)

add_executable(hid_report_policy_test hid_report_policy_test.cpp)
target_compile_features(hid_report_policy_test PRIVATE cxx_std_20)
target_include_directories(hid_report_policy_test PRIVATE ../src)

enable_testing()
add_test(NAME hid_report_policy COMMAND hid_report_policy_test)
