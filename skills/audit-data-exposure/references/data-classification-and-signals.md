# Data classification and signals

Use this reference to classify candidates without treating a regex match as a finding. Personal data is contextual: separate values can identify a person when combined, and pseudonymized data can remain re-identifiable.

## Method anchors

- [European Commission: Data protection explained](https://commission.europa.eu/law/law-topic/data-protection/data-protection-explained_en) describes personal data, combined identifiers, pseudonymization, and irreversible anonymization.
- [NIST SP 800-122](https://csrc.nist.gov/pubs/sp/800/122/final) provides context-based guidance for identifying and protecting personally identifiable information.
- [NIST IR 8053](https://csrc.nist.gov/pubs/ir/8053/final) covers de-identification and re-identification risk across structured data, free text, images, and other media.
- [Presidio documentation](https://presidio.dataprivacystack.org/) explicitly warns that automated detection cannot guarantee discovery of every sensitive value.

Use these as review methods, not jurisdiction-specific legal conclusions.

## Candidate classes

Review direct and indirect identifiers, including:

- names, aliases, signatures, faces, voices, and biographical free text;
- personal email, phone, postal address, precise location, IP address, cookie/device/advertising identifiers, usernames, and account IDs;
- government, tax, health, insurance, education, employment, financial, payment, biometric, and genetic identifiers or records;
- dates of birth, event timestamps, rare demographics, job titles, geographic detail, and other quasi-identifiers that become identifying in combination;
- customer, patient, employee, applicant, contributor, household, contact, analytics, support, and telemetry records;
- credentials, session tokens, private keys, recovery material, signed URLs, and secret-bearing configuration;
- confidential business records, private endpoints, internal hostnames, tenant identifiers, unpublished incidents, and proprietary datasets;
- developer-machine usernames, home directories, private mount points, local database paths, network shares, editor/session files, and diagnostic output;
- personal data embedded in comments, documentation, examples, tests, snapshots, logs, screenshots, notebooks, generated output, archives, databases, or file names.

## Public and synthetic evidence

Treat an identity as intentionally public only when repository evidence establishes its purpose, such as:

- repository owner or organization handles;
- author/publisher names in manifests;
- explicit public support or security contact channels;
- license/copyright attribution and ordinary contributor metadata;
- project, documentation, issue, and source URLs.

Do not automatically permit a personal address, phone number, private email, local path, or unrelated identity merely because it belongs to the owner or can be found online.

Strong synthetic evidence includes reserved example domains, documentation IP ranges, obvious placeholders, deterministic generators, and a documented fixture contract. A fictional-looking name or altered identifier alone is weak evidence. Verify that synthetic records were generated independently rather than lightly edited from real records.

## Re-identification and anonymization

- Treat encryption, reversible tokenization, keyed lookup, stable hashing, and maintained re-identification maps as protections or pseudonymization, not anonymization.
- Evaluate uniqueness, population size, rare combinations, timestamps, free text, geolocation, and linkability to public or private auxiliary data.
- Treat a dataset as irreversibly anonymous only when the repository contains credible methodology and the relevant attack/linkage assumptions have been evaluated. The audit normally reports evidence and risk rather than certifying anonymity.
- Inspect transformation code and tests for values preserved accidentally in logs, errors, rejected-record files, backups, checkpoints, or mapping tables.

## Disposable migration signals

Flag apparently single-use artifacts regardless of whether they embed private values:

- names or comments such as `one-off`, `run once`, `temporary`, `delete after`, `backfill`, `repair`, `convert my data`, or `manual migration`;
- hard-coded source/destination paths, concrete record IDs, literal identity maps, local usernames, personal directories, tenant IDs, or date-bounded special cases;
- scripts outside maintained migration infrastructure with no supported invocation, tests, rollback, idempotency, ownership, or lifecycle documentation;
- abandoned import/export programs, notebook cells, SQL scratch files, disabled jobs, commented commands, and ad hoc repair utilities;
- migration inputs, outputs, rejected rows, backup copies, and before/after snapshots.

Do not flag solely because an artifact transforms data when it is a maintained repeatable schema migration, supported upgrade path, reusable import/export tool, fixture generator, or product-owned operational job. Verify its lifecycle rather than trusting its directory name.

## Confidence discipline

- `high`: direct repository evidence establishes real or private data, an active credential, re-identification, or explicit one-time intent.
- `medium`: multiple contextual signals support exposure but identity, authenticity, or lifecycle is not fully established.
- `low`: pattern or filename signal needs local contextual review.

Never downgrade direct evidence merely because exploitation or re-identification was not attempted. Never upgrade a detector match without validating its context.
