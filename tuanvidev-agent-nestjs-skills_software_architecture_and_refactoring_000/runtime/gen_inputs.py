import os
import json
from pathlib import Path

WORKSPACE = Path("/workspace")

# ── directory skeleton ──────────────────────────────────────────────────────
dirs = [
    "src/patients",
    "src/patients/dto",
    "src/patients/entities",
    "src/auth",
    "src/common/filters",
    "src/common/interceptors",
    "src/common/guards",
    "src/config",
    "src/database",
    "test",
    "docs",
    "scripts",
    "dist",
]
for d in dirs:
    (WORKSPACE / d).mkdir(parents=True, exist_ok=True)

# ── package.json ────────────────────────────────────────────────────────────
pkg = {
    "name": "patient-records-api",
    "version": "0.1.0",
    "description": "Healthcare patient records API",
    "scripts": {
        "build": "tsc",
        "start": "node dist/main.js",
        "start:dev": "ts-node src/main.ts"
    },
    "dependencies": {
        "@nestjs/common": "^10.0.0",
        "@nestjs/core": "^10.0.0",
        "@nestjs/platform-express": "^10.0.0",
        "@nestjs/jwt": "^10.0.0",
        "@nestjs/passport": "^10.0.0",
        "passport": "^0.6.0",
        "passport-jwt": "^4.0.0",
        "class-transformer": "^0.5.1",
        "class-validator": "^0.14.0",
        "reflect-metadata": "^0.1.13",
        "rxjs": "^7.8.0",
        "typeorm": "^0.3.17",
        "sqlite3": "^5.1.6"
    },
    "devDependencies": {
        "@types/node": "^20.0.0",
        "typescript": "^5.0.0"
    }
}
(WORKSPACE / "package.json").write_text(json.dumps(pkg, indent=2))

# ── tsconfig.json ───────────────────────────────────────────────────────────
tsconfig = {
    "compilerOptions": {
        "module": "commonjs",
        "declaration": True,
        "removeComments": True,
        "emitDecoratorMetadata": True,
        "experimentalDecorators": True,
        "allowSyntheticDefaultImports": True,
        "target": "ES2021",
        "sourceMap": True,
        "outDir": "./dist",
        "baseUrl": "./",
        "incremental": True,
        "skipLibCheck": True,
        "strictNullChecks": False,
        "noImplicitAny": False,
        "strictBindCallApply": False,
        "forceConsistentCasingInFileNames": False,
        "noFallthroughCasesInSwitch": False
    }
}
(WORKSPACE / "tsconfig.json").write_text(json.dumps(tsconfig, indent=2))

# ── BROKEN main.ts ──────────────────────────────────────────────────────────
# Missing: ValidationPipe globally, ClassSerializerInterceptor globally
(WORKSPACE / "src/main.ts").write_text("""\
import 'reflect-metadata';
import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);
  // TODO: wire up global validation and serialization
  await app.listen(3000);
}
bootstrap();
""")

# ── BROKEN app.module.ts ────────────────────────────────────────────────────
# Missing feature-module structure; everything dumped in one module
(WORKSPACE / "src/app.module.ts").write_text("""\
import { Module } from '@nestjs/common';
import { PatientsController } from './patients/patients.controller';
import { GodService } from './patients/god.service';

@Module({
  imports: [],
  controllers: [PatientsController],
  providers: [GodService],
})
export class AppModule {}
""")

# ── BROKEN god.service.ts ────────────────────────────────────────────────────
# Violates: arch-use-repository-pattern, arch-single-responsibility,
#           di-prefer-constructor-injection (uses property injection),
#           di-use-interfaces-tokens (no token used),
#           error handling done inline with raw try-catch + console.log
(WORKSPACE / "src/patients/god.service.ts").write_text("""\
import { Injectable, Inject } from '@nestjs/common';
import { EntityManager } from 'typeorm';
import { JwtService } from '@nestjs/jwt';

@Injectable()
export class GodService {
  // WRONG: property injection instead of constructor injection
  @Inject()
  private entityManager: EntityManager;

  @Inject()
  private jwtService: JwtService;

  async getAllPatients() {
    try {
      // WRONG: direct EntityManager usage instead of repository pattern
      return await this.entityManager.query('SELECT * FROM patient');
    } catch (e) {
      console.log('error', e);
      return [];
    }
  }

  async getPatientById(id: number) {
    try {
      const results = await this.entityManager.query(
        'SELECT * FROM patient WHERE id = ?', [id]
      );
      return results[0] || null;
    } catch (e) {
      console.log(e);
      throw e;
    }
  }

  async createPatient(data: any) {
    // WRONG: no validation, raw any type, no transaction
    return await this.entityManager.query(
      'INSERT INTO patient (name, dob, ssn, diagnosis) VALUES (?, ?, ?, ?)',
      [data.name, data.dob, data.ssn, data.diagnosis]
    );
  }

  async validateUser(username: string, password: string) {
    // mixed concerns: auth logic in the same service
    if (username === 'admin' && password === 'password') {
      return { id: 1, username: 'admin' };
    }
    return null;
  }

  async generateToken(user: any) {
    return this.jwtService.sign({ sub: user.id, username: user.username });
  }
}
""")

# ── BROKEN patients.controller.ts ───────────────────────────────────────────
# Violates: no guards, no pipes, no DTO serialization, returns raw entities
(WORKSPACE / "src/patients/patients.controller.ts").write_text("""\
import { Controller, Get, Post, Param, Body } from '@nestjs/common';
import { GodService } from './god.service';

@Controller('patients')
export class PatientsController {
  constructor(private readonly godService: GodService) {}

  @Get()
  async findAll() {
    return this.godService.getAllPatients();
  }

  @Get(':id')
  async findOne(@Param('id') id: string) {
    return this.godService.getPatientById(parseInt(id));
  }

  @Post()
  async create(@Body() body: any) {
    // WRONG: accepts any body with no validation
    return this.godService.createPatient(body);
  }
}
""")

# ── BROKEN / missing DTO files ───────────────────────────────────────────────
# create-patient.dto.ts has no class-validator decorators and uses plain types
(WORKSPACE / "src/patients/dto/create-patient.dto.ts").write_text("""\
// WRONG: no validation decorators
export class CreatePatientDto {
  name: string;
  dob: string;
  ssn: string;
  diagnosis: string;
}
""")

# patient-response.dto.ts does not exist yet (agent must create it)
# (intentionally absent)

# ── BROKEN patient entity ────────────────────────────────────────────────────
(WORKSPACE / "src/patients/entities/patient.entity.ts").write_text("""\
import { Entity, PrimaryGeneratedColumn, Column } from 'typeorm';

@Entity()
export class Patient {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  name: string;

  @Column()
  dob: string;

  // sensitive fields exposed directly - no serialization control
  @Column()
  ssn: string;

  @Column()
  diagnosis: string;
}
""")

# ── Empty placeholder files that signal "missing implementation" ─────────────
(WORKSPACE / "src/common/filters/.gitkeep").write_text("")
(WORKSPACE / "src/common/interceptors/.gitkeep").write_text("")
(WORKSPACE / "src/common/guards/.gitkeep").write_text("")
(WORKSPACE / "src/auth").mkdir(exist_ok=True)
(WORKSPACE / "src/auth/auth.service.ts").write_text("""\
// Stub - auth service not yet implemented
export class AuthService {}
""")

# ── Distractor files ─────────────────────────────────────────────────────────
(WORKSPACE / "docs/api-spec.md").write_text("""\
# Patient Records API

## Endpoints

POST /auth/login  - authenticate
GET  /patients    - list patients
GET  /patients/:id - get patient
POST /patients    - create patient

## Notes
- SSN must never be returned in API responses
- All endpoints except /auth/login require a valid bearer token
""")

(WORKSPACE / "docs/data-model.md").write_text("""\
# Data Model

Patient:
  id: number (PK)
  name: string
  dob: string (ISO 8601)
  ssn: string (sensitive - never expose)
  diagnosis: string
""")

(WORKSPACE / "scripts/seed.sql").write_text("""\
INSERT INTO patient (name, dob, ssn, diagnosis) VALUES
('Alice Smith', '1985-03-12', '123-45-6789', 'Hypertension'),
('Bob Jones',   '1972-07-04', '987-65-4321', 'Diabetes Type 2');
""")

(WORKSPACE / "scripts/migrate.sh").write_text("""\
#!/bin/bash
echo "Running migrations..."
""")

(WORKSPACE / "test/app.e2e-spec.ts").write_text("""\
// TODO: implement e2e tests
""")

(WORKSPACE / "dist/.gitkeep").write_text("")

# Config distractor
(WORKSPACE / "src/config/configuration.ts").write_text("""\
export default () => ({
  port: parseInt(process.env.PORT, 10) || 3000,
  jwtSecret: process.env.JWT_SECRET || 'CHANGE_ME_IN_PRODUCTION',
});
""")

(WORKSPACE / "src/database/database.module.ts").write_text("""\
import { Module } from '@nestjs/common';

@Module({})
export class DatabaseModule {}
""")

print("Workspace generated successfully.")
print("Files created:")
for f in sorted(WORKSPACE.rglob("*")):
    if f.is_file():
        print(f"  {f.relative_to(WORKSPACE)}")