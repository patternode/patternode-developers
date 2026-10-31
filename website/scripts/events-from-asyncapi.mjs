// Writes docs/events/ from ../specs/asyncapi.yaml: an index of every event, and one page per
// message, so the events reference is plain Markdown that search, llms.txt and agents can read.
// Generated; do not edit the output. Run by `npm run gen:events` before start and build.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import YAML from 'yaml';

const here = path.dirname(fileURLToPath(import.meta.url));
const specPath = path.resolve(here, '../../specs/asyncapi.yaml');
const outDir = path.resolve(here, '../docs/events');
const spec = YAML.parse(fs.readFileSync(specPath, 'utf8'));

const messages = spec.components.messages;
const channelsOf = (key) =>
  Object.entries(spec.channels)
    .filter(([, ch]) => Object.values(ch.messages || {}).some((m) => m.$ref === `#/components/messages/${key}`))
    .map(([name]) => name);

const cell = (s) => String(s ?? '').replace(/\|/g, '\\|').replace(/\n+/g, ' ').trim();
const slug = (name) => name.replace(/[^a-z0-9]+/gi, '-').toLowerCase();
const typeOf = (p) => (p.$ref ? p.$ref.split('/').pop().replace('.schema.json', '') : p.const !== undefined ? `\`${p.const}\`` : p.type ?? '');

function propertiesTable(payload) {
  const props = payload?.properties ?? {};
  const required = new Set(payload?.required ?? []);
  if (!Object.keys(props).length) return '';
  const rows = Object.entries(props).map(
    ([k, p]) => `| \`${k}\` | ${cell(typeOf(p))} | ${required.has(k) ? 'Yes' : ''} | ${cell(p.description)} |`,
  );
  return ['| Field | Type | Required | Description |', '|---|---|---|---|', ...rows].join('\n');
}

fs.rmSync(outDir, {recursive: true, force: true});
fs.mkdirSync(outDir, {recursive: true});

const front = (o) => `---\n${Object.entries(o).map(([k, v]) => `${k}: ${JSON.stringify(v)}`).join('\n')}\n---\n\n`;
const header = '<!-- Generated from specs/asyncapi.yaml by website/scripts/events-from-asyncapi.mjs. Do not edit. -->\n\n';

const rows = [];
let position = 1;
for (const [key, m] of Object.entries(messages)) {
  const name = m.name ?? key;
  const channels = channelsOf(key);
  const status = m['x-status'] ?? 'available';
  rows.push(`| [\`${name}\`](./${slug(name)}.md) | ${cell(m.title)} | ${channels.map((c) => `\`${c}\``).join(', ')} | ${status} |`);
  const example = m.examples?.[0]?.payload;
  const body = [
    `# ${name}`,
    '',
    cell(m.title) + '.',
    '',
    '| | |',
    '|---|---|',
    `| Status | ${status} |`,
    `| Channels | ${channels.map((c) => `\`${c}\``).join(', ')} |`,
    '',
    m.summary ? cell(m.summary) + '\n' : '',
    '## Payload',
    '',
    propertiesTable(m.payload),
    '',
    example ? '## Example\n\n```json\n' + JSON.stringify(example, null, 2) + '\n```\n' : '',
  ].join('\n');
  fs.writeFileSync(
    path.join(outDir, `${slug(name)}.md`),
    front({title: name, sidebar_position: position++, description: cell(m.title)}) + header + body,
  );
}

const intro = cell(spec.info.description.split('\n\n')[0]);
fs.writeFileSync(
  path.join(outDir, 'index.md'),
  front({title: 'Events', sidebar_position: 0, description: 'Every event Patternode sends, on webhooks, subscriptions and event buses.'}) +
    header +
    [
      '# Events',
      '',
      intro,
      '',
      'Webhook deliveries are signed to Standard Webhooks; see [Receiving webhooks](../guides/webhooks.mdx). Every event has a stable `id` to deduplicate on, and stream events a `sequence` to order on ([Real-time](../service/realtime.md)). The contract is [`/specs/asyncapi.yaml`](pathname:///specs/asyncapi.yaml).',
      '',
      '| Event | What | Channels | Status |',
      '|---|---|---|---|',
      ...rows,
      '',
    ].join('\n'),
);
console.log(`events: ${Object.keys(messages).length} pages in ${path.relative(process.cwd(), outDir)}`);
