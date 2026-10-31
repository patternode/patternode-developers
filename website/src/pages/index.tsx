import React from 'react';
import Link from '@docusaurus/Link';
import Layout from '@theme/Layout';
import useBaseUrl from '@docusaurus/useBaseUrl';
import SignalLine from '../components/SignalLine';
import ContextDiagram from '@site/docs/architecture/img/context.svg';
import styles from './index.module.css';

const EXTEND = `curl https://api.patternode.com/v1/segmentations/extend \\
  -H "authorization: Bearer $PATTERNODE_API_KEY" \\
  -H "x-amz-content-sha256: $BODY_SHA256" \\
  -d '{"series": "exu/7f3a/1b02/export-kw",
       "profile": "standard@2026-11",
       "edge": "pne1.…",
       "bars": [[1730250000000, 1730253599000,
                 428.1, 441.0, 420.3, 436.7]]}'`;

const FACTS: [string, string][] = [
  ['0', 'series kept at Patternode'],
  ['1', 'contract, every plan and industry'],
  ['ns', 'timestamps, kept exactly'],
  ['99.99%', 'availability on Mission Critical'],
];

const PRODUCTS = [
  {name: 'Delve', what: 'The shards toolkit', line: 'Any time series in, its segments at every level out: for galleries, live tiles and search.', status: 'Available', mark: true},
  {name: 'Essence', what: 'What repeats', line: 'Patterns by precedent, read from the same segments.', status: 'Planned'},
  {name: 'Sentinel', what: 'What moves', line: 'Anomalies by shape, and the alarm on them.', status: 'Planned'},
  {name: 'Foresight', what: 'What comes next', line: 'Forecasting, drawn at the same levels as the history.', status: 'Planned'},
];

const PATHS = [
  {to: '/get-started/quickstart', who: 'Partner engineer', title: 'Make a call in a minute', body: 'Run the mock, call it, read the answer. No account needed.'},
  {to: '/architecture', who: 'Enterprise architect', title: 'The architecture, from outside', body: 'Parties, boundaries, data, residency and resilience on one page.'},
  {to: '/architecture/integration', who: 'Solution architect', title: 'Design the integration', body: 'Four integration styles, your side, and the decisions you make.'},
  {to: '/playbooks/delve-onboarding', who: 'Project lead', title: 'From order to go-live', body: 'Eleven gated stages, from choosing a plan to production traffic.'},
  {to: '/architecture/quant', who: 'Quant fund', title: 'Research and live, one contract', body: 'Backtests that agree with live trading, and a latency budget.'},
  {to: '/industries/utilities', who: 'Utility', title: 'Outbound only, outside OT', body: 'Historian data in, nothing into your operational network.'},
];

export default function Home(): JSX.Element {
  const delveMark = useBaseUrl('/img/products/delve-reverse.svg');
  return (
    <Layout title="Build on the shape of every series" description="Patternode for developers: the API contract, examples, playbooks and architecture for integrating with Delve.">
      <header className={styles.hero}>
        <SignalLine />
        <div className={`container ${styles.heroInner}`}>
          <div className={styles.heroText}>
            <p className={styles.eyebrow}>patternode · developers</p>
            <h1 className={styles.title}>Build on the shape of every series.</h1>
            <p className={styles.lede}>
              Delve turns any time series into segments at every level, so every chart draws what it can read and
              every system can act as a shape closes. One API, one contract, and none of your data kept.
            </p>
            <div className={styles.ctas}>
              <Link className={styles.primary} to="/get-started/quickstart">Quickstart</Link>
              <Link className={styles.secondary} to="/architecture">Architecture</Link>
              <Link className={styles.tertiary} to="/get-started/access">Get access →</Link>
            </div>
          </div>
          <div className={styles.code} aria-label="An example request">
            <div className={styles.codeBar}>
              <span>POST /v1/segmentations/extend</span>
              <span className={styles.codeTag}>edge + bars in · segments + edge out</span>
            </div>
            <pre>{EXTEND}</pre>
          </div>
        </div>
      </header>

      <section className={styles.facts}>
        <div className="container">
          <ul>
            {FACTS.map(([n, label]) => (
              <li key={label}><span className={styles.factNumber}>{n}</span><span>{label}</span></li>
            ))}
          </ul>
        </div>
      </section>

      <main>
        <section className={`container ${styles.section}`}>
          <h2>One API, four products, one foundation</h2>
          <p className={styles.sectionLede}>Integrate once. Essence, Sentinel and Foresight will read the segments Delve gives you.</p>
          <div className={styles.products}>
            {PRODUCTS.map((p) => (
              <div key={p.name} className={`${styles.product} ${p.mark ? styles.productLead : ''}`}>
                <div className={styles.productHead}>
                  {p.mark ? <img src={delveMark} alt="" width={40} height={40} /> : <span className={styles.productDot} />}
                  <div>
                    <h3>{p.name}</h3>
                    <span className={styles.productWhat}>{p.what}</span>
                  </div>
                  <span className={p.status === 'Available' ? styles.statusOn : styles.statusPlanned}>{p.status}</span>
                </div>
                <p>{p.line}</p>
              </div>
            ))}
          </div>
        </section>

        <section className={`container ${styles.section}`}>
          <h2>Start where you are</h2>
          <div className={styles.paths}>
            {PATHS.map((p) => (
              <Link key={p.to} to={p.to} className={styles.path}>
                <span className={styles.pathWho}>{p.who}</span>
                <h3>{p.title}</h3>
                <p>{p.body}</p>
              </Link>
            ))}
          </div>
        </section>

        <section className={`container ${styles.section}`}>
          <div className={styles.split}>
            <div>
              <h2>Your side, your data</h2>
              <p>
                Your backend calls Patternode; Patternode never calls into your network. Bars go out under names you
                make up, segments come back, and for a forming series a sealed edge comes back too, for you to store and
                send with the next bars. Patternode keeps none of it.
              </p>
              <ul className={styles.ticks}>
                <li>REST on every plan; gRPC and event buses on Mission Critical</li>
                <li>Exactly-once in effect: the same edge and bars give the same answer</li>
                <li>Your jurisdiction: Australia and New Zealand, the EU or the US</li>
                <li>Contracts in OpenAPI, AsyncAPI and gRPC, tested in CI</li>
              </ul>
              <Link className={styles.inlineLink} to="/architecture/partner-side">See the reference architecture →</Link>
            </div>
            <Link to="/architecture" className={styles.diagram}>
              <ContextDiagram role="img" aria-label="Patternode from the outside: your client, you, and Patternode, with what crosses between them" />
            </Link>
          </div>
        </section>

        <section className={styles.contracts}>
          <div className="container">
            <h2>The contract is the documentation</h2>
            <p>Generate a client, point an agent at it, or read it. These are the files CI tests against.</p>
            <div className={styles.chips}>
              <a href={useBaseUrl('/specs/openapi.yaml')}>openapi.yaml</a>
              <a href={useBaseUrl('/specs/asyncapi.yaml')}>asyncapi.yaml</a>
              <a href="https://github.com/patternode/patternode-developers/tree/main/specs/proto">delve.proto</a>
              <a href={useBaseUrl('/llms.txt')}>llms.txt</a>
              <a href="https://github.com/patternode/patternode-developers">GitHub</a>
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}
