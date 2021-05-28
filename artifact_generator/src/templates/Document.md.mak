# Id
${doc_info.id}

<%text>## Document Type</%text>
${doc_info.ssm_doc_type}

% if doc_info.doc_type != 'util':
<%text>## Description</%text>
${doc_info.description}

<%text>## Disruption Type</%text>
${doc_info.failureType}

<%text>## Risk</%text>
${doc_info.risk}

<%text>## Permissions required</%text>
% for permission in doc_info.permissions:
    * ${permission}
% endfor

<%text>## Depends On</%text>
% if not doc_info.depends_on:
None
% else:
% for dependency in doc_info.depends_on:
    * ${dependency}
% endfor
% endif

% if doc_info.doc_type == 'test':
<%text>## Supports Rollback</%text>
${doc_info.is_rollback}

<%text>## Recommended Alarms</%text>
% if not doc_info.alarms:
None
% else:
% for key, value in doc_info.alarms.items():
    * ${key} : ${value}
% endfor
% endif

% endif
% endif
<%text>## Inputs</%text>
%if not doc_info.inputs:
None
% else:
% for key, value in doc_info.inputs.items():
<%text>### </%text>`${key}`
    * type: ${value['type']}
    * description: ${value['description']}
% endfor
% endif

<%text>## Outputs</%text>
%if not doc_info.outputs:
None
% else:
% for output in doc_info.outputs:
    * `${output}`
% endfor
%endif
