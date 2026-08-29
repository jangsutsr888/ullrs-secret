Feedback and issue reporting
============================

Feedback is welcome. If Ullr's Secret produces a surprising chart, an importer
rejects valid data, the documentation leaves a question unanswered, or you
have an idea that would make the tool more useful, please open an issue in the
`GitHub issue tracker <https://github.com/jangsutsr888/ullrs-secret/issues>`_.

Before opening an issue
-----------------------

Search the existing issues first. If someone has already reported the same
problem or idea, add useful context there rather than creating a duplicate.
For behavior questions, also review :doc:`limitations` and the page for the
relevant :doc:`chart command <charts/index>` or
:doc:`weather importer <importers/index>`.

Reporting a bug
---------------

A reproducible report is much easier to investigate. Include as much of the
following as is practical:

* the output of ``python --version`` and
  ``python -c "import ullrs_secret; print(ullrs_secret.__version__)"``;
* your operating system and installation method;
* the complete ``ullrs-secret`` command, with secrets and private paths
  removed;
* the importer and weather model involved, if applicable;
* the expected behavior and the actual behavior;
* the complete traceback or error message; and
* a minimal weather JSON file or chart image when it helps demonstrate the
  problem.

Weather files and commands can reveal precise coordinates and trip plans.
Remove any location information you do not want to publish. Never include API
tokens, passwords, CDS credentials, session cookies, or other secrets in a
GitHub issue.

Suggesting an improvement
-------------------------

Feature requests, documentation corrections, model questions, and reports
from real-world use are all useful. Explain the decision or workflow you are
trying to support, what you expected the tool to provide, and why the proposed
change would help. Concrete examples are especially valuable, even when you do
not yet have an implementation in mind.

.. warning::

   GitHub issues are for improving the software, not for obtaining immediate
   backcountry safety advice. Ullr's Secret is not an avalanche forecast and
   an issue response should never be treated as a go/no-go travel decision.
