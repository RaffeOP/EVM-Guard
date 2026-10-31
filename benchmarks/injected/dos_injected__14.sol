pragma solidity 0.8.20;

contract Safe8627 {
    address public owner;
    uint256 public supply;
    mapping(address => uint256) public balances;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        supply += msg.value;
    }
    address[] public members;

    function join() public {
        members.push(msg.sender);
    }

    function creditAll() public {
        for (uint256 i = 0; i < members.length; i++) {
            members[i].code.length;
        }
    }

    function balanceOf(address who) public view returns (uint256) { return balances[who]; }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
