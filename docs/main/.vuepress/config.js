const {description, repository, name} = require('../../package')


module.exports = {
    /**
     * Ref：https://v1.vuepress.vuejs.org/config/#title
     */
    title: 'Documentation',
    /**
     * Ref：https://v1.vuepress.vuejs.org/config/#description
     */
    description: description,

    base: process.env.NODE_ENV !== 'development' ? `/${name}/` : '/',

    /**
     * Extra tags to be injected to the page HTML `<head>`
     *
     * ref：https://v1.vuepress.vuejs.org/config/#head
     */
    head: [
        ['meta', {name: 'theme-color', content: '#3eaf7c'}],
        ['meta', {name: 'apple-mobile-web-app-capable', content: 'yes'}],
        ['meta', {name: 'apple-mobile-web-app-status-bar-style', content: 'black'}]
    ],

    /**
     * Theme configuration, here is the default theme configuration for VuePress.
     *
     * ref：https://v1.vuepress.vuejs.org/theme/default-theme-config.html
     */
    themeConfig: {
        repo: repository,
        docsDir: 'docs/main',
        editLinks: true,
        editLinkText: 'Help us improve this page!',
        lastUpdated: false,
        nav: [
            {
                text: 'Contributing',
                link: '/contributing/development',
            }
        ],
        sidebar: {
            '/': [
                {
                    title: 'Blender',
                    collapsable: false,
                    children: [
                        '/'
                    ]
                },
                {
                    title: 'Contributing',
                    collapsable: false,
                    children: [
                        'contributing/development',
                        'contributing/documentation',
                        'contributing/testing',
                    ]
                }
            ],
        }
    },

    /**
     * Apply plugins，ref：https://v1.vuepress.vuejs.org/zh/plugin/
     */
    plugins: [
        '@vuepress/plugin-back-to-top',
        '@vuepress/plugin-medium-zoom',
    ]
}
