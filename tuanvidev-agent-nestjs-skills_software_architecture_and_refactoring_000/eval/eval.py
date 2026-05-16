import sys
import json
import re
from pathlib import Path

def load_file(path: Path):
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return None

def find_files(workspace: Path, name: str):
    return list(workspace.rglob(name))

def check(name: str, passed: bool, detail: str):
    return {"name": name, "passed": passed, "detail": detail}

def run_eval(workspace_str: str):
    workspace = Path(workspace_str)
    checks = []

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 1: Feature module exists for patients
    # arch-feature-modules: PatientsModule must exist as its own @Module
    # ──────────────────────────────────────────────────────────────────────────
    patients_module_files = find_files(workspace, "patients.module.ts")
    if not patients_module_files:
        checks.append(check("patients_module_exists", False,
            "patients.module.ts not found anywhere in workspace"))
    else:
        content = load_file(patients_module_files[0]) or ""
        has_module_decorator = bool(re.search(r'@Module\s*\(', content))
        exports_controller = "PatientsController" in content
        checks.append(check("patients_module_exists", has_module_decorator and exports_controller,
            f"patients.module.ts found at {patients_module_files[0]}. "
            f"Has @Module: {has_module_decorator}, references PatientsController: {exports_controller}"))

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 2: AppModule imports PatientsModule (not raw controller/god-service)
    # arch-feature-modules: AppModule should import feature module
    # ──────────────────────────────────────────────────────────────────────────
    app_module_files = find_files(workspace, "app.module.ts")
    if not app_module_files:
        checks.append(check("app_module_imports_feature_module", False, "app.module.ts not found"))
    else:
        content = load_file(app_module_files[0]) or ""
        imports_patients_module = bool(re.search(r'PatientsModule', content))
        still_has_god_service = bool(re.search(r'GodService', content))
        checks.append(check("app_module_imports_feature_module",
            imports_patients_module and not still_has_god_service,
            f"PatientsModule in AppModule imports: {imports_patients_module}, "
            f"GodService still directly in AppModule: {still_has_god_service}"))

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 3: Repository pattern – a repository service/class injected via token
    # arch-use-repository-pattern + di-use-interfaces-tokens
    # Must have an injection token (string or Symbol) for the repository
    # ──────────────────────────────────────────────────────────────────────────
    all_ts_files = list(workspace.rglob("*.ts"))
    repo_token_found = False
    repo_token_detail = "No injection token for repository found"
    for f in all_ts_files:
        content = load_file(f) or ""
        # Look for a constant token like PATIENT_REPOSITORY or similar InjectionToken pattern
        if re.search(r'(PATIENT_REPOSITORY|PATIENTS_REPOSITORY|PATIENT_REPO|InjectionToken|provide\s*:\s*[\'"]PATIENT)', content, re.IGNORECASE):
            repo_token_found = True
            repo_token_detail = f"Repository injection token found in {f.relative_to(workspace)}"
            break
    checks.append(check("repository_injection_token", repo_token_found, repo_token_detail))

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 4: Constructor injection in service(s) - no property @Inject()
    # di-prefer-constructor-injection: god service pattern with @Inject on props must be gone
    # ──────────────────────────────────────────────────────────────────────────
    property_injection_found = False
    property_injection_detail = "No property injection (@Inject on class fields) found - good"
    service_files = list(workspace.rglob("*.service.ts"))
    for f in service_files:
        content = load_file(f) or ""
        # Pattern: @Inject() on a line followed by private/public/protected field (not constructor param)
        if re.search(r'@Inject\(\)[\s\n]+(?:private|public|protected|readonly)\s+\w+\s*:', content):
            property_injection_found = True
            property_injection_detail = f"Property injection still present in {f.relative_to(workspace)}"
            break
    checks.append(check("no_property_injection", not property_injection_found, property_injection_detail))

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 5: DTO with class-validator decorators
    # security-validate-all-input: CreatePatientDto must use @IsString, @IsNotEmpty, etc.
    # ──────────────────────────────────────────────────────────────────────────
    dto_files = find_files(workspace, "create-patient.dto.ts")
    if not dto_files:
        checks.append(check("dto_has_validation_decorators", False, "create-patient.dto.ts not found"))
    else:
        content = load_file(dto_files[0]) or ""
        has_is_string = bool(re.search(r'@IsString\b', content))
        has_is_not_empty = bool(re.search(r'@IsNotEmpty\b', content))
        has_class_validator_import = bool(re.search(r'class-validator', content))
        passed = has_class_validator_import and (has_is_string or has_is_not_empty)
        checks.append(check("dto_has_validation_decorators", passed,
            f"class-validator import: {has_class_validator_import}, "
            f"@IsString: {has_is_string}, @IsNotEmpty: {has_is_not_empty}"))

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 6: Response DTO with @Exclude and @Expose (serialization)
    # api-use-dto-serialization: patient response must exclude SSN
    # ──────────────────────────────────────────────────────────────────────────
    response_dto_files = (
        find_files(workspace, "patient-response.dto.ts") +
        find_files(workspace, "patient.response.dto.ts") +
        find_files(workspace, "patient.dto.ts")
    )
    # Also check entity for @Exclude
    entity_files = find_files(workspace, "patient.entity.ts")
    
    serialization_ok = False
    serialization_detail = "No response DTO with @Exclude/@Expose found"
    
    for f in response_dto_files + entity_files:
        content = load_file(f) or ""
        has_exclude = bool(re.search(r'@Exclude\b', content))
        has_expose = bool(re.search(r'@Expose\b', content))
        has_class_transformer = bool(re.search(r'class-transformer', content))
        if has_exclude and has_class_transformer:
            serialization_ok = True
            serialization_detail = (
                f"Serialization decorators found in {f.relative_to(workspace)}: "
                f"@Exclude={has_exclude}, @Expose={has_expose}"
            )
            break
    checks.append(check("response_dto_serialization", serialization_ok, serialization_detail))

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 7: Global exception filter (custom @Catch filter)
    # error-use-exception-filters: must have a class decorated with @Catch
    # ──────────────────────────────────────────────────────────────────────────
    filter_files = find_files(workspace, "*.filter.ts")
    exception_filter_ok = False
    exception_filter_detail = "No custom exception filter (*.filter.ts with @Catch) found"
    for f in filter_files:
        content = load_file(f) or ""
        if re.search(r'@Catch\b', content) and re.search(r'ExceptionFilter', content):
            exception_filter_ok = True
            exception_filter_detail = f"Exception filter with @Catch found in {f.relative_to(workspace)}"
            break
    checks.append(check("custom_exception_filter", exception_filter_ok, exception_filter_detail))

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 8: JWT Guard using @UseGuards or registered globally
    # security-use-guards + security-auth-jwt
    # ──────────────────────────────────────────────────────────────────────────
    guard_files = find_files(workspace, "*.guard.ts") + find_files(workspace, "jwt-auth.guard.ts") + find_files(workspace, "jwt.guard.ts")
    jwt_guard_ok = False
    jwt_guard_detail = "No JWT guard file found"
    
    for f in guard_files:
        content = load_file(f) or ""
        if (re.search(r'@Injectable', content) and 
            re.search(r'(AuthGuard|CanActivate|JwtStrategy|passport-jwt|jwt)', content, re.IGNORECASE)):
            jwt_guard_ok = True
            jwt_guard_detail = f"JWT guard found in {f.relative_to(workspace)}"
            break
    
    if not jwt_guard_ok:
        # Also check if AuthGuard('jwt') is used in controller
        for f in find_files(workspace, "*.controller.ts"):
            content = load_file(f) or ""
            if re.search(r"AuthGuard\(['\"]jwt['\"]", content):
                jwt_guard_ok = True
                jwt_guard_detail = f"AuthGuard('jwt') used in {f.relative_to(workspace)}"
                break
    checks.append(check("jwt_guard_implemented", jwt_guard_ok, jwt_guard_detail))

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 9: UseGuards applied to patients controller
    # security-use-guards: controller must be protected
    # ──────────────────────────────────────────────────────────────────────────
    controller_files = find_files(workspace, "patients.controller.ts")
    guard_on_controller = False
    guard_controller_detail = "patients.controller.ts not found or @UseGuards not applied"
    if controller_files:
        content = load_file(controller_files[0]) or ""
        guard_on_controller = bool(re.search(r'@UseGuards\b', content))
        guard_controller_detail = (
            f"patients.controller.ts @UseGuards present: {guard_on_controller}"
        )
    checks.append(check("guard_on_patients_controller", guard_on_controller, guard_controller_detail))

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 10: ValidationPipe registered globally in main.ts
    # api-use-pipes + security-validate-all-input
    # ──────────────────────────────────────────────────────────────────────────
    main_files = find_files(workspace, "main.ts")
    validation_pipe_global = False
    validation_pipe_detail = "main.ts not found or ValidationPipe not registered globally"
    if main_files:
        content = load_file(main_files[0]) or ""
        has_validation_pipe = bool(re.search(r'ValidationPipe', content))
        has_use_global_pipes = bool(re.search(r'useGlobalPipes', content))
        validation_pipe_global = has_validation_pipe and has_use_global_pipes
        validation_pipe_detail = (
            f"ValidationPipe present: {has_validation_pipe}, "
            f"useGlobalPipes called: {has_use_global_pipes}"
        )
    checks.append(check("global_validation_pipe", validation_pipe_global, validation_pipe_detail))

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 11: ClassSerializerInterceptor registered globally or on controller
    # api-use-dto-serialization: must be wired up for @Exclude to work
    # ──────────────────────────────────────────────────────────────────────────
    serializer_interceptor_ok = False
    serializer_detail = "ClassSerializerInterceptor not found in main.ts or any module"
    
    for f in find_files(workspace, "main.ts") + find_files(workspace, "*.module.ts"):
        content = load_file(f) or ""
        if re.search(r'ClassSerializerInterceptor', content):
            serializer_interceptor_ok = True
            serializer_detail = f"ClassSerializerInterceptor found in {f.relative_to(workspace)}"
            break
    checks.append(check("class_serializer_interceptor_registered", serializer_interceptor_ok, serializer_detail))

    # ──────────────────────────────────────────────────────────────────────────
    # CHECK 12: God service removed or split (no longer a single god service)
    # arch-single-responsibility: GodService must be split
    # ──────────────────────────────────────────────────────────────────────────
    god_service_files = find_files(workspace, "god.service.ts")
    god_service_gone_or_split = True
    god_service_detail = "god.service.ts not present - correctly removed"
    
    if god_service_files:
        content = load_file(god_service_files[0]) or ""
        # If it still has everything mixed together (JWT + EntityManager + patient logic)
        has_jwt = bool(re.search(r'JwtService', content))
        has_entity_manager = bool(re.search(r'entityManager\.query', content))
        has_property_inject = bool(re.search(r'@Inject\(\)[\s\n]+(?:private|public|protected)', content))
        still_god = has_jwt and has_entity_manager
        god_service_gone_or_split = not still_god
        god_service_detail = (
            f"god.service.ts still exists with mixed concerns: "
            f"JWT+EntityManager together={still_god}, "
            f"property injection={has_property_inject}"
        )
    checks.append(check("god_service_split_or_removed", god_service_gone_or_split, god_service_detail))

    # ──────────────────────────────────────────────────────────────────────────
    # SCORING
    # ──────────────────────────────────────────────────────────────────────────
    total = len(checks)
    passed_count = sum(1 for c in checks if c["passed"])
    score = round(passed_count / total, 4)
    all_passed = passed_count == total

    result = {
        "passed": all_passed,
        "score": score,
        "checks": checks
    }
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    workspace = sys.argv[1] if len(sys.argv) > 1 else "/workspace"
    run_eval(workspace)