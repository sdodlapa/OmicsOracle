# OmicsOracle Event Flow and Testing Framework

## Overview

This document provides an introduction to the OmicsOracle event flow and testing/validation framework. The framework maps all events from server startup to frontend display, along with their corresponding test/validation files.

## Purpose

The purpose of this framework is to:

1. **Visualize the System**: Provide a clear visual representation of how data flows through the OmicsOracle system
2. **Map Testing Coverage**: Show which parts of the system are covered by tests
3. **Identify Gaps**: Highlight areas that need additional testing or monitoring
4. **Guide Development**: Serve as a reference for developers working on the system
5. **Ensure Robustness**: Facilitate comprehensive testing and validation

## Documentation Components

The framework consists of the following components:

1. **GraphViz Flow Diagram** (`docs/event_flow_validation.dot`): Detailed graph showing all events and test files
2. **Event Flow and Validation Map** (`docs/EVENT_FLOW_VALIDATION_MAP.md`): Comprehensive documentation of all events and test files
3. **Event Flow Chart** (`docs/EVENT_FLOW_CHART.md`): Simplified Mermaid diagrams for quick reference

## How to Use This Framework

### For Developers

1. **Before Adding Features**: Understand the current event flow and testing coverage
2. **When Adding New Components**: Add corresponding test files and update the diagrams
3. **For Debugging**: Use the diagrams to trace the flow of data and identify potential issues

### For Testers

1. **Test Coverage Analysis**: Identify which tests to run for specific components
2. **Test Development**: Use the framework as a guide for writing new tests
3. **Regression Testing**: Ensure that all events are properly tested after changes

### For System Administrators

1. **Monitoring Setup**: Configure monitoring based on the monitoring components in the diagrams
2. **Issue Diagnosis**: Use the diagrams to pinpoint where issues might be occurring
3. **Performance Optimization**: Focus on key events for performance improvements

## Key Events Overview

The OmicsOracle system can be divided into three main phases:

1. **Server Initialization Phase**:
   - Server startup
   - Configuration loading
   - NCBI email configuration
   - Pipeline initialization
   - Component initialization
   - API routes setup

2. **Search Process Phase**:
   - Search request handling
   - Query parsing
   - GEO database search
   - Result processing
   - AI summarization
   - Result formatting

3. **Frontend Rendering Phase**:
   - WebSocket connection
   - Progress updates
   - Results display
   - Error handling

Each of these phases has corresponding test files and monitoring components as detailed in the documentation.

## Using the Visualization Files

### GraphViz Diagram

The GraphViz diagram (`docs/event_flow_validation.dot`) can be rendered using:

1. **GraphViz Command Line**:
   ```
   dot -Tpng docs/event_flow_validation.dot -o event_flow.png
   ```

2. **Online GraphViz Tools**:
   - Visit [WebGraphviz](http://www.webgraphviz.com/)
   - Copy and paste the contents of the .dot file

### Mermaid Diagrams

The Mermaid diagrams in `docs/EVENT_FLOW_CHART.md` can be viewed:

1. **In GitHub**: GitHub natively renders Mermaid diagrams in Markdown
2. **In VS Code**: Use a Markdown preview extension that supports Mermaid
3. **Online Mermaid Editor**: Visit [Mermaid Live Editor](https://mermaid.live/)

## Next Steps

1. **Complete Test Implementation**: Implement any missing test files identified in the diagrams
2. **Expand Monitoring Coverage**: Enhance monitoring for key events
3. **Automate Testing**: Configure CI/CD to run the test suite automatically
4. **Improve Visualization**: Refine the diagrams based on system changes
5. **Document Best Practices**: Add more detailed testing and monitoring best practices

---

This event flow and testing framework is a living document. As the OmicsOracle system evolves, the framework should be updated to reflect changes and improvements.
