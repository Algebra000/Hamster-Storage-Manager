import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const buildDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(buildDir, '..');
const inputFile = path.join(projectRoot, 'frontend', 'classify_shower_video.js');
const outputFile = path.join(projectRoot, 'frontend', 'classify_shower_video.min.js');

// classify_shower.js creates this class directly as a classic-script global.
// It must keep its spelling when top-level mangling is enabled.
const exportedNames = [
    'CS_VideoWidget',
];

const npxCommand = process.platform === 'win32' ? 'npx.cmd' : 'npx';
const mangleOptions = `toplevel,reserved=[${exportedNames.join(',')}]`;
const terserArgs = [
    '--yes',
    'terser@5.51.2',
    inputFile,
    '--compress',
    'passes=2',
    '--mangle',
    mangleOptions,
    '--format',
    'comments=false',
    '--output',
    outputFile,
];
const command = process.platform === 'win32'
    ? (process.env.ComSpec || 'cmd.exe')
    : npxCommand;
const commandArgs = process.platform === 'win32'
    ? ['/d', '/s', '/c', npxCommand, ...terserArgs]
    : terserArgs;
const result = spawnSync(
    command,
    commandArgs,
    {
        cwd: projectRoot,
        encoding: 'utf8',
        stdio: 'inherit',
    },
);

if (result.error) {
    throw result.error;
}
if (result.status !== 0) {
    throw new Error(`Terser export failed with exit code ${result.status}`);
}

console.log(`Exported: ${path.relative(projectRoot, outputFile)}`);
console.log(`Reserved globals: ${exportedNames.join(', ')}`);
