pragma solidity 0.8.20;

contract Escrow1321 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public deposits;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        deposits[msg.sender] += msg.value;
        supply += msg.value;
    }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
