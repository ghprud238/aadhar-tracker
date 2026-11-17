// Learn more https://docs.expo.io/guides/customizing-metro
const { getDefaultConfig } = require('expo/metro-config');

const config = getDefaultConfig(__dirname);

// Exclude native Android, iOS, git, and build artifact trees from Metro file watcher
config.resolver.blockList = [
  /.*\/android\/.*/,
  /.*\/ios\/.*/,
  /.*\.git\/.*/,
  /.*\/coverage\/.*/,
];

module.exports = config;
