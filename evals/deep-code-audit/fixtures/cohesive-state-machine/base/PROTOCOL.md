# Transfer protocol

The peer must negotiate before it can transfer data. A dropped connection enters recovery and must resume through the ready transfer boundary. Completion requires at least one acknowledged chunk. Complete and failed states are terminal. The explicit states are part of the interoperability contract and must not be replaced with independent booleans.
