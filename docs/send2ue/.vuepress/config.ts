const {description, repository, name} = require('../../package')
import { defaultTheme } from '@vuepress/theme-default'
import { defineUserConfig } from '@vuepress/cli'
import { palettePlugin } from '@vuepress/plugin-palette'
// @ts-ignore
import { googleAnalyticsPlugin } from '@vuepress/plugin-google-analytics'


export default defineUserConfig({
    title: 'Send to Unreal',
    description: description,
    // @ts-ignore
    base: process.env.PROD === '1' ? `/${name}/` : '/',

    theme: defaultTheme({
        repo: repository,
        docsDir: 'docs/send2ue',
        editLinkText: 'Help us improve this page!',
        lastUpdated: false,

        navbar: [
            {
                text: 'Home',
                link: process.env.PROD === '1' ? 'https://epicgames.github.io/BlenderTools/' : '/',
                target:'_self',
                // rel:false
            }
        ],
        sidebar: {
            '/': [
                {
                    text: 'Introduction',
                    children: [
                        '/introduction/quickstart'
                    ]
                },
                {
                    text: 'Asset Types',
                    children: [
                        '/asset-types/skeletal-mesh',
                        '/asset-types/static-mesh',
                        '/asset-types/animation'
                    ]
                },
                {
                    text: 'Settings',
                    children: [
                        '/settings/paths',
                        '/settings/export',
                        '/settings/import',
                        '/settings/validations',
                    ]
                },
                {
                    text: 'Customize',
                    children: [
                        '/customize/templates',
                        '/customize/python-api',
                        '/customize/extensions'
                    ]
                },
                {
                    text: 'Extras',
                    children: [
                        '/extras/pipeline-menu',
                        '/extras/addon-preferences',
                        '/extras/supported-extensions',
                        '/extras/community-extensions',
                    ]
                },
                {
                    text: 'Trouble Shooting',
                    children: [
                        '/trouble-shooting/faq',
                        '/trouble-shooting/errors',
                    ]
                }
            ],
        }
    }),
    plugins: [
        palettePlugin({preset: 'sass'}),
        googleAnalyticsPlugin({id: process.env.GA_ID})
    ]
})

