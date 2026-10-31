pragma solidity 0.5.12;

contract Escrow5754 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public balances;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        supply += msg.value;
    }

    function balanceOf(address who) public view returns (uint256) { return balances[who]; }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
