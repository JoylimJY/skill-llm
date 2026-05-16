#!/usr/bin/env node
import { MemoryPalaceManager } from '../dist/src/manager.js';
import { ExperienceManager } from '../dist/src/experience-manager.js';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Workspace path from env or default
const workspacePath = process.env.OPENCLAW_WORKSPACE || process.env.HOME + '/.openclaw/workspace';

// Show help if no args or --help
if (!process.argv[2] || process.argv[2] === '--help' || process.argv[2] === '-h') {
  console.log(`
Memory Palace CLI - Cognitive enhancement layer for OpenClaw agents

Usage: npx memory-palace <action> [params]

Actions:
  write <content> [location] [tags] [importance] [type]
  get <id>
  update <id> <content> [tags] [importance]
  delete <id>
  search <query> [tags] [top_k]
  list [location]
  stats
  restore <id>
  record_experience <content> <applicability> <source> [category]
  get_experiences [category] [verified]
  verify_experience <id> <effective>

Examples:
  npx memory-palace write "User prefers dark mode" preferences '["ui"]' 0.8
  npx memory-palace search "preferences"
  npx memory-palace record_experience "Use TypeScript" "TS projects" "dev-team" development
`);
  process.exit(0);
}

const manager = new MemoryPalaceManager({ workspaceDir: workspacePath });
const expManager = new ExperienceManager(manager);

const action = process.argv[2];

async function main() {
  let result;
  
  try {
    switch (action) {
      case 'write': {
        const content = process.argv[3];
        if (!content) throw new Error('content is required');
        const location = process.argv[4] || 'default';
        const tags = process.argv[5] ? JSON.parse(process.argv[5]) : undefined;
        const importance = process.argv[6] ? parseFloat(process.argv[6]) : undefined;
        const type = process.argv[7] || undefined;
        result = await manager.store({ content, location, tags, importance, type });
        break;
      }
      case 'get': {
        const id = process.argv[3];
        if (!id) throw new Error('id is required');
        result = await manager.get(id);
        break;
      }
      case 'update': {
        const id = process.argv[3];
        const content = process.argv[4];
        if (!id || !content) throw new Error('id and content are required');
        const tags = process.argv[5] ? JSON.parse(process.argv[5]) : undefined;
        const importance = process.argv[6] ? parseFloat(process.argv[6]) : undefined;
        result = await manager.update({ id, content, tags, importance });
        break;
      }
      case 'delete': {
        const id = process.argv[3];
        if (!id) throw new Error('id is required');
        result = await manager.delete(id);
        break;
      }
      case 'search': {
        const query = process.argv[3];
        if (!query) throw new Error('query is required');
        const tags = process.argv[4] ? JSON.parse(process.argv[4]) : undefined;
        const topK = process.argv[5] ? parseInt(process.argv[5]) : 10;
        result = await manager.recall(query, { tags, topK });
        break;
      }
      case 'list': {
        const location = process.argv[3] || undefined;
        result = await manager.list({ location });
        break;
      }
      case 'stats': {
        result = await manager.stats();
        break;
      }
      case 'restore': {
        const id = process.argv[3];
        if (!id) throw new Error('id is required');
        result = await manager.restore(id);
        break;
      }
      case 'record_experience': {
        const content = process.argv[3];
        const applicability = process.argv[4];
        const source = process.argv[5];
        if (!content || !applicability || !source) {
          throw new Error('content, applicability, and source are required');
        }
        const category = process.argv[6] || 'general';
        result = await expManager.recordExperience({ content, category, applicability, source });
        break;
      }
      case 'get_experiences': {
        const category = process.argv[3] || undefined;
        const verified = process.argv[4] ? process.argv[4] === 'true' : undefined;
        result = await expManager.getExperiences({ category, verified });
        break;
      }
      case 'verify_experience': {
        const id = process.argv[3];
        const effective = process.argv[4] === 'true';
        if (!id) throw new Error('id is required');
        result = await expManager.verifyExperience({ id, effective });
        break;
      }
      default:
        throw new Error(`Unknown action: ${action}. Use --help for usage.`);
    }
    
    console.log(JSON.stringify(result, null, 2));
  } catch (err) {
    console.error('Error:', err.message);
    process.exit(1);
  }
}

main();
