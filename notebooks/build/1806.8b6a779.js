"use strict";(self.webpackChunk_JUPYTERLAB_CORE_OUTPUT=self.webpackChunk_JUPYTERLAB_CORE_OUTPUT||[]).push([[1806,4715],{54715:(e,t,n)=>{n.r(t),n.d(t,{STATUSBAR_PLUGIN_ID:()=>g,default:()=>C,kernelStatus:()=>h,lineColItem:()=>b,runningSessionsItem:()=>I});var a=n(22715),s=n(45030),o=n(53700),i=n(14318),r=n(5997),l=n(71829),c=n(32248),d=n(49718),u=n(58618),m=n(90375);const g="@jupyterlab/statusbar-extension:plugin",p={id:g,requires:[d.ITranslator],provides:c.IStatusBar,autoStart:!0,activate:(e,t,n,a,s)=>{const o=t.load("jupyterlab"),i=new c.StatusBar;i.id="jp-main-statusbar",e.shell.add(i,"bottom"),n&&n.layoutModified.connect((()=>{i.update()}));const r=o.__("Main Area"),l="statusbar:toggle";if(e.commands.addCommand(l,{label:o.__("Show Status Bar"),execute:e=>{i.setHidden(i.isVisible),a&&a.set(g,"visible",i.isVisible)},isToggled:()=>i.isVisible}),s&&s.addItem({command:l,category:r}),a){const t=a.load(g),n=e=>{const t=e.get("visible").composite;i.setHidden(!t)};Promise.all([t,e.restored]).then((([e])=>{n(e),e.changed.connect((e=>{n(e)}))})).catch((e=>{console.error(e.message)}))}return i},optional:[a.ILabShell,l.ISettingRegistry,s.ICommandPalette]},h={id:"@jupyterlab/statusbar-extension:kernel-status",autoStart:!0,requires:[c.IStatusBar,r.INotebookTracker,o.IConsoleTracker,a.ILabShell,d.ITranslator],optional:[s.ISessionContextDialogs],activate:(e,t,n,a,o,i,r)=>{let l=null;const d=new c.KernelStatus({onClick:async()=>{l&&await(r||s.sessionContextDialogs).selectKernel(l,i)}},i),u=e=>{d.model.activityName=e.label};o.currentChanged.connect(((e,t)=>{const{oldValue:s,newValue:o}=t;s&&s.title.changed.disconnect(u),o&&o.title.changed.connect(u),l=o&&a.has(o)||o&&n.has(o)?o.sessionContext:null,d.model.sessionContext=l})),t.registerStatusItem("@jupyterlab/statusbar-extension:kernel-status",{item:d,align:"left",rank:1,isActive:()=>{const e=o.currentWidget;return!!e&&(n.has(e)||a.has(e))}})}},b={id:"@jupyterlab/statusbar-extension:line-col-status",autoStart:!0,requires:[c.IStatusBar,r.INotebookTracker,i.IEditorTracker,o.IConsoleTracker,a.ILabShell,d.ITranslator],activate:(e,t,n,a,s,o,i)=>{const r=new c.LineCol(i),l=(e,t)=>{r.model.editor=t&&t.editor},d=(e,t)=>{r.model.editor=t&&t.editor};o.currentChanged.connect(((e,t)=>{const{oldValue:o,newValue:i}=t;if(o&&s.has(o)?o.console.promptCellCreated.disconnect(d):o&&n.has(o)&&o.content.activeCellChanged.disconnect(l),i&&s.has(i)){i.console.promptCellCreated.connect(d);const e=i.console.promptCell;r.model.editor=e&&e.editor}else if(i&&n.has(i)){i.content.activeCellChanged.connect(l);const e=i.content.activeCell;r.model.editor=e&&e.editor}else i&&a.has(i)?r.model.editor=i.content.editor:r.model.editor=null})),t.registerStatusItem("@jupyterlab/statusbar-extension:line-col-status",{item:r,align:"right",rank:2,isActive:()=>{const e=o.currentWidget;return!!e&&(n.has(e)||a.has(e)||s.has(e))}})}},I={id:"@jupyterlab/statusbar-extension:running-sessions-status",autoStart:!0,requires:[c.IStatusBar,d.ITranslator],activate:(e,t,n)=>{const a=new c.RunningSessions({onClick:()=>e.shell.activateById("jp-running-sessions"),serviceManager:e.serviceManager,translator:n});t.registerStatusItem("@jupyterlab/statusbar-extension:running-sessions-status",{item:a,align:"left",rank:0})}},S={id:"@jupyterlab/statusbar-extension:mode-switch",requires:[a.ILabShell,d.ITranslator,c.IStatusBar],optional:[l.ISettingRegistry],activate:(e,t,n,a,s)=>{const o=n.load("jupyterlab"),i=new u.Switch;if(i.id="jp-single-document-mode",i.valueChanged.connect(((e,n)=>{t.mode=n.newValue?"single-document":"multiple-document"})),t.modeChanged.connect(((e,t)=>{i.value="single-document"===t})),s){const n=s.load(g),a=e=>{const n=e.get("startMode").composite;n&&(t.mode="single"===n?"single-document":"multiple-document")};Promise.all([n,e.restored]).then((([e])=>{a(e)})).catch((e=>{console.error(e.message)}))}i.value="single-document"===t.mode;const r=()=>{const t=e.commands.keyBindings.find((e=>"application:toggle-mode"===e.command));if(t){const e=t.keys.map(m.CommandRegistry.formatKeystroke).join(", ");i.caption=o.__("Simple Interface (%1)",e)}else i.caption=o.__("Simple Interface")};r(),e.commands.keyBindingChanged.connect((()=>{r()})),i.label=o.__("Simple"),a.registerStatusItem("@jupyterlab/statusbar-extension:mode-switch",{item:i,align:"left",rank:-1})},autoStart:!0},C=[p,b,h,I,S]}}]);
//# sourceMappingURL=1806.8b6a779.js.map