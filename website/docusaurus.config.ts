// developers.patternode.com. The site is built from three sources in this repository, so
// what it shows is what is specified and tested:
//   website/docs/   the guides, playbooks and service contract (Markdown and MDX)
//   ../specs/       the contracts; the API reference and events pages are generated from them
//   ../examples/, ../terraform/   code, embedded into pages at build time with raw-loader
import path from 'node:path';
import fs from 'node:fs';
import {themes as prismThemes} from 'prism-react-renderer';
import type {Config, Plugin} from '@docusaurus/types';
import type * as Preset from '@docusaurus/preset-classic';
import type * as OpenApiPlugin from 'docusaurus-plugin-openapi-docs';

const repo = path.resolve(__dirname, '..');

// Lets a page import a real file: import src from '!!raw-loader!@examples/python/first_call.py'.
const repoAliases = (): Plugin => ({
  name: 'repo-aliases',
  configureWebpack: () => ({
    resolve: {
      alias: {
        '@examples': path.join(repo, 'examples'),
        '@terraform': path.join(repo, 'terraform'),
        '@specs': path.join(repo, 'specs'),
      },
    },
  }),
});

// Publishes the contracts unchanged at /specs/, where agents and code generators fetch them.
const publishSpecs = () => ({
  name: 'publish-specs',
  async postBuild({outDir}: {outDir: string}) {
    fs.cpSync(path.join(repo, 'specs'), path.join(outDir, 'specs'), {recursive: true});
  },
});

const config: Config = {
  title: 'Patternode for developers',
  tagline: 'Integrate with Delve and the products that run on it',
  favicon: 'img/favicon.svg',
  url: process.env.SITE_URL || 'https://developers.patternode.com',
  baseUrl: process.env.SITE_BASE_URL || '/',
  organizationName: 'patternode',
  projectName: 'patternode-developers',
  trailingSlash: false,

  // v4 defaults now, and the Rspack bundler (@docusaurus/faster) for build speed.
  future: {v4: true, faster: true},

  onBrokenLinks: 'throw',
  onBrokenAnchors: 'throw',
  onDuplicateRoutes: 'throw',

  markdown: {
    // .md is CommonMark, .mdx is MDX: pages that embed code from the repository are .mdx.
    format: 'detect',
    mermaid: true,
    hooks: {onBrokenMarkdownLinks: 'throw', onBrokenMarkdownImages: 'throw'},
  },

  i18n: {defaultLocale: 'en', locales: ['en']},

  presets: [
    [
      'classic',
      {
        docs: {
          path: 'docs',
          routeBasePath: '/',
          sidebarPath: './sidebars.ts',
          docItemComponent: '@theme/ApiItem',
          editUrl: 'https://github.com/patternode/patternode-developers/edit/main/website/',
          showLastUpdateTime: false,
        },
        blog: false,
        theme: {customCss: './src/css/custom.css'},
        sitemap: {changefreq: 'weekly'},
      } satisfies Preset.Options,
    ],
  ],

  plugins: [
    repoAliases,
    publishSpecs,
    'docusaurus-plugin-sass',
    [
      'docusaurus-plugin-openapi-docs',
      {
        id: 'openapi',
        docsPluginId: 'classic',
        config: {
          patternode: {
            specPath: '../specs/openapi.yaml',
            outputDir: 'docs/api',
            sidebarOptions: {groupPathsBy: 'tag'},
            showSchemas: true,
          } satisfies OpenApiPlugin.Options,
        },
      },
    ],
    [
      'docusaurus-plugin-llms',
      {
        title: 'Patternode for developers',
        description:
          'Integrate with Patternode. Build and test against the mock (mock/mock_patternode.py) first; ' +
          'the specs at /specs/ are the contract; never put an API key in code, a file, a log or a chat.',
        generateLLMsTxt: true,
        generateLLMsFullTxt: true,
        generateMarkdownFiles: true,
        excludeImports: true,
        removeDuplicateHeadings: true,
      },
    ],
  ],

  themes: [
    '@docusaurus/theme-mermaid',
    'docusaurus-theme-openapi-docs',
    [
      '@easyops-cn/docusaurus-search-local',
      {hashed: true, indexBlog: false, docsRouteBasePath: '/', highlightSearchTermsOnTargetPage: true},
    ],
  ],

  themeConfig: {
    colorMode: {respectPrefersColorScheme: true},
    navbar: {
      title: 'Developers',
      logo: {alt: 'Patternode', src: 'img/logo.svg', srcDark: 'img/logo-reverse.svg'},
      items: [
        {type: 'docSidebar', sidebarId: 'docs', label: 'Docs', position: 'left'},
        {to: '/architecture', label: 'Architecture', position: 'left'},
        {type: 'docSidebar', sidebarId: 'api', label: 'API reference', position: 'left'},
        {to: '/events', label: 'Events', position: 'left'},
        {to: '/service', label: 'Service contract', position: 'left'},
        {to: '/industries', label: 'Industries', position: 'left'},
        {href: 'https://github.com/patternode/patternode-developers', label: 'GitHub', position: 'right'},
      ],
    },
    footer: {
      style: 'dark',
      links: [
        {
          title: 'Start',
          items: [
            {label: 'Quickstart', to: '/get-started/quickstart'},
            {label: 'Onboarding playbook', to: '/playbooks/delve-onboarding'},
          ],
        },
        {
          title: 'Contracts',
          items: [
            {label: 'OpenAPI', href: 'pathname:///specs/openapi.yaml'},
            {label: 'AsyncAPI', href: 'pathname:///specs/asyncapi.yaml'},
            {label: 'llms.txt', href: 'pathname:///llms.txt'},
          ],
        },
        {
          title: 'Patternode',
          items: [
            {label: 'patternode.com', href: 'https://patternode.com'},
            {label: 'Status', href: 'https://status.patternode.com'},
          ],
        },
      ],
      copyright: `© ${new Date().getFullYear()} Patternode. Docs CC BY 4.0; code and specs Apache 2.0. Patternode and Delve are Patternode's marks.`,
    },
    languageTabs: [
      {highlight: 'bash', language: 'curl', logoClass: 'curl'},
      {highlight: 'python', language: 'python', logoClass: 'python', variant: 'requests'},
      {highlight: 'javascript', language: 'nodejs', logoClass: 'nodejs', variant: 'native'},
      {highlight: 'go', language: 'go', logoClass: 'go'},
      {highlight: 'java', language: 'java', logoClass: 'java', variant: 'unirest'},
    ],
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ['bash', 'json', 'yaml', 'protobuf', 'hcl', 'python', 'typescript', 'go', 'java'],
    },
  } satisfies Preset.ThemeConfig,
};

export default config;
